"""
Network flow feature extraction.

Converts a list of raw Scapy packets into the 41-feature vector expected
by the trained Random Forest models.  Features are derived following the
same definitions used during training (see FINAL_FEATURES.csv).
"""

import statistics

from scapy.layers.inet import UDP, TCP, IP

from server.config import L7_PROTO_MAP, WEB_PORTS


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Division that returns *default* when the denominator is zero."""
    return a / b if b else default


def _iat_stats(times: list[float]) -> tuple[float, float, float, float]:
    """Return (min, max, avg, stdev) of inter-arrival times in milliseconds."""
    if len(times) < 2:
        return 0.0, 0.0, 0.0, 0.0
    iats = [(times[i] - times[i - 1]) * 1000 for i in range(1, len(times))]
    return (
        min(iats),
        max(iats),
        statistics.mean(iats),
        statistics.stdev(iats) if len(iats) > 1 else 0.0,
    )


def _count_tcp_retransmissions(pkts: list) -> int:
    """Heuristic retransmission count based on duplicate TCP sequence numbers."""
    seen_seq: set[int] = set()
    retrans = 0
    for pkt in pkts:
        if pkt.haslayer(TCP):
            seq = pkt[TCP].seq
            if seq in seen_seq:
                retrans += 1
            else:
                seen_seq.add(seq)
    return retrans


def extract_features(
    packets,
    client_ip: str,
    server_port: int,
) -> dict[str, float | int]:
    """
    Derive the 41 model features from captured Scapy packets.

    Traffic is split into two directions:
        src → dst  =  client → server  (inbound to the server)
        dst → src  =  server → client  (outbound from the server)
    """

    # ── Split packets by direction ──────────────────────────────────────
    src_to_dst: list = []
    dst_to_src: list = []

    for pkt in packets:
        if not pkt.haslayer(IP):
            continue
        if pkt[IP].src == client_ip:
            src_to_dst.append(pkt)
        else:
            dst_to_src.append(pkt)

    all_pkts = src_to_dst + dst_to_src
    total_pkts = len(all_pkts)

    # ── Timestamps ──────────────────────────────────────────────────────
    src_times = sorted(float(p.time) for p in src_to_dst) if src_to_dst else []
    dst_times = sorted(float(p.time) for p in dst_to_src) if dst_to_src else []

    # ── Packet sizes ────────────────────────────────────────────────────
    src_sizes = [len(p) for p in src_to_dst]
    dst_sizes = [len(p) for p in dst_to_src]
    all_sizes = src_sizes + dst_sizes

    # ── L4 ports & protocol (from first available packet) ───────────────
    l4_src_port = 0
    l4_dst_port = server_port
    protocol = 6  # default TCP

    for pkt in src_to_dst or dst_to_src or all_pkts:
        if pkt.haslayer(IP):
            protocol = pkt[IP].proto
        if pkt.haslayer(TCP):
            l4_src_port = pkt[TCP].sport
            l4_dst_port = pkt[TCP].dport
        elif pkt.haslayer(UDP):
            l4_src_port = pkt[UDP].sport
            l4_dst_port = pkt[UDP].dport
        break  # only need the first packet

    l7_proto = L7_PROTO_MAP.get(l4_dst_port, 0)

    # ── Packet counts ──────────────────────────────────────────────────
    in_pkts = len(src_to_dst)
    out_pkts = len(dst_to_src)  # zero-division handled by _safe_div

    # ── TCP flags from server side ──────────────────────────────────────
    server_tcp_flags = 0
    for pkt in dst_to_src:
        if pkt.haslayer(TCP):
            server_tcp_flags |= int(pkt[TCP].flags)

    # ── Duration (milliseconds) ─────────────────────────────────────────
    duration_in = (src_times[-1] - src_times[0]) * \
        1000 if len(src_times) > 1 else 0
    duration_out = (dst_times[-1] - dst_times[0]) * \
        1000 if len(dst_times) > 1 else 0

    # ── TTL ─────────────────────────────────────────────────────────────
    ttls = [pkt[IP].ttl for pkt in all_pkts if pkt.haslayer(IP)]
    max_ttl = max(ttls) if ttls else 0

    # ── Packet sizes (extremes) ─────────────────────────────────────────
    shortest_flow_pkt = min(all_sizes) if all_sizes else 0
    longest_flow_pkt = max(all_sizes) if all_sizes else 0
    min_ip_pkt_len = shortest_flow_pkt

    # ── Byte totals ─────────────────────────────────────────────────────
    in_bytes = sum(src_sizes) if src_sizes else 0
    out_bytes = sum(dst_sizes) if dst_sizes else 0

    # ── Throughput ──────────────────────────────────────────────────────
    total_duration_sec = 0.0
    if src_times and dst_times:
        total_duration_sec = (
            max(src_times[-1], dst_times[-1]) - min(src_times[0], dst_times[0])
        )
    elif src_times:
        total_duration_sec = src_times[-1] - src_times[0]
    elif dst_times:
        total_duration_sec = dst_times[-1] - dst_times[0]

    dst_to_src_second_bytes = _safe_div(out_bytes, total_duration_sec)
    src_to_dst_avg_throughput = _safe_div(in_bytes * 8, total_duration_sec)
    dst_to_src_avg_throughput = _safe_div(out_bytes * 8, total_duration_sec)

    # ── Retransmissions ─────────────────────────────────────────────────
    retransmitted_in_pkts = _count_tcp_retransmissions(src_to_dst)
    retransmitted_out_pkts = _count_tcp_retransmissions(dst_to_src)

    # ── Packet size distribution buckets ────────────────────────────────
    num_up_to_128 = sum(1 for s in all_sizes if s <= 128)
    num_128_256 = sum(1 for s in all_sizes if 128 < s <= 256)
    num_256_512 = sum(1 for s in all_sizes if 256 < s <= 512)
    num_512_1024 = sum(1 for s in all_sizes if 512 < s <= 1024)
    num_1024_1514 = sum(1 for s in all_sizes if 1024 < s <= 1514)

    # ── TCP window max ──────────────────────────────────────────────────
    tcp_win_max_in = max(
        (pkt[TCP].window for pkt in src_to_dst if pkt.haslayer(TCP)),
        default=0,
    )
    tcp_win_max_out = max(
        (pkt[TCP].window for pkt in dst_to_src if pkt.haslayer(TCP)),
        default=0,
    )

    # ── Inter-arrival times ─────────────────────────────────────────────
    src_iat_min, src_iat_max, src_iat_avg, src_iat_std = _iat_stats(src_times)
    dst_iat_min, dst_iat_max, dst_iat_avg, dst_iat_std = _iat_stats(dst_times)

    # ── Engineered features ─────────────────────────────────────────────
    is_web_port = int(l4_dst_port in WEB_PORTS or l4_src_port in WEB_PORTS)
    pkts_ratio = _safe_div(in_pkts, out_pkts)
    bytes_per_pkt_in = _safe_div(in_bytes, in_pkts)
    bytes_per_pkt_out = _safe_div(out_bytes, out_pkts)
    pkt_size_range = longest_flow_pkt - shortest_flow_pkt
    retrans_rate_in = _safe_div(retransmitted_in_pkts, in_pkts)
    retrans_rate_out = _safe_div(retransmitted_out_pkts, out_pkts)
    throughput_ratio = _safe_div(
        src_to_dst_avg_throughput, dst_to_src_avg_throughput)
    iat_avg_ratio = _safe_div(src_iat_avg, dst_iat_avg)

    flow_duration_ms = max(duration_in, duration_out)
    duration_per_pkt = _safe_div(flow_duration_ms, total_pkts)
    small_pkt_ratio = _safe_div(num_up_to_128, total_pkts)

    # ── Assemble feature dict (order matches FEATURE_NAMES) ─────────────
    return {
        "L4_SRC_PORT": l4_src_port,
        "L4_DST_PORT": l4_dst_port,
        "PROTOCOL": protocol,
        "L7_PROTO": l7_proto,
        "IN_PKTS": in_pkts,
        "SERVER_TCP_FLAGS": server_tcp_flags,
        "DURATION_IN": duration_in,
        "DURATION_OUT": duration_out,
        "MAX_TTL": max_ttl,
        "SHORTEST_FLOW_PKT": shortest_flow_pkt,
        "MIN_IP_PKT_LEN": min_ip_pkt_len,
        "DST_TO_SRC_SECOND_BYTES": dst_to_src_second_bytes,
        "RETRANSMITTED_IN_PKTS": retransmitted_in_pkts,
        "RETRANSMITTED_OUT_PKTS": retransmitted_out_pkts,
        "SRC_TO_DST_AVG_THROUGHPUT": src_to_dst_avg_throughput,
        "DST_TO_SRC_AVG_THROUGHPUT": dst_to_src_avg_throughput,
        "NUM_PKTS_UP_TO_128_BYTES": num_up_to_128,
        "NUM_PKTS_128_TO_256_BYTES": num_128_256,
        "NUM_PKTS_256_TO_512_BYTES": num_256_512,
        "NUM_PKTS_512_TO_1024_BYTES": num_512_1024,
        "NUM_PKTS_1024_TO_1514_BYTES": num_1024_1514,
        "TCP_WIN_MAX_IN": tcp_win_max_in,
        "TCP_WIN_MAX_OUT": tcp_win_max_out,
        "SRC_TO_DST_IAT_MIN": src_iat_min,
        "SRC_TO_DST_IAT_MAX": src_iat_max,
        "SRC_TO_DST_IAT_STDDEV": src_iat_std,
        "DST_TO_SRC_IAT_MIN": dst_iat_min,
        "DST_TO_SRC_IAT_MAX": dst_iat_max,
        "DST_TO_SRC_IAT_AVG": dst_iat_avg,
        "DST_TO_SRC_IAT_STDDEV": dst_iat_std,
        "IS_WEB_PORT": is_web_port,
        "PKTS_RATIO": pkts_ratio,
        "BYTES_PER_PKT_IN": bytes_per_pkt_in,
        "BYTES_PER_PKT_OUT": bytes_per_pkt_out,
        "PKT_SIZE_RANGE": pkt_size_range,
        "RETRANS_RATE_IN": retrans_rate_in,
        "RETRANS_RATE_OUT": retrans_rate_out,
        "THROUGHPUT_RATIO": throughput_ratio,
        "IAT_AVG_RATIO": iat_avg_ratio,
        "DURATION_PER_PKT": duration_per_pkt,
        "SMALL_PKT_RATIO": small_pkt_ratio,
    }

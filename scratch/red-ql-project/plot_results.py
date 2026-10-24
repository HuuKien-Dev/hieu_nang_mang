import os
import numpy as np
import matplotlib.pyplot as plt

RESULTS_DIR = "scratch/red-ql-project/results/"
PLOTS_DIR = "scratch/red-ql-project/plots/"
os.makedirs(PLOTS_DIR, exist_ok=True)

# 1. Vẽ Figure 1: Đường cong xác suất đánh rơi gói tin của RED-QL
min_th, max_th, max_p = 30.0, 90.0, 0.1
target_ql = 2.0 * (max_th + min_th) / 3.0 - min_th

def pb_red_ql(ave):
    if ave < min_th: return 0.0
    elif ave < target_ql:
        return 9.0 * max_p * ((ave - min_th) / (2.0 * (max_th - 2.0 * min_th)))**2
    elif ave < max_th:
        return max_p + 3.0 * (1.0 - max_p) * ((ave - target_ql) / (max_th + min_th))
    else: return 1.0

ave_x = np.linspace(0, 100, 500)
pb_y = [pb_red_ql(x) for x in ave_x]

plt.figure(figsize=(6.5, 4.8), dpi=300)
plt.plot(ave_x, pb_y, color='#7a0019', linewidth=2, label='RED-QL')
plt.xlabel('Average Queue Size')
plt.ylabel('Packet Dropping Probability')
plt.xlim(0, 100)
plt.ylim(0, 1.0)
plt.legend(loc='upper left', frameon=True, edgecolor='black')
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "Figure_1_RED_QL_Curve.png"))
plt.close()

# 2. Vẽ Figure 3, 4, 5 từ dữ liệu thực nghiệm ns-3
styles = {
    'RED':    {'color': '#b22222', 'ls': ':',  'lw': 1.8},
    'NLRED':  {'color': '#000080', 'ls': '-.', 'lw': 1.8},
    'SmRED':  {'color': '#cc00cc', 'ls': '-',  'lw': 1.8},
    'RED-QL': {'color': '#000000', 'ls': '--', 'lw': 1.8}
}

scenarios = [("Light", 3), ("Moderate", 4), ("Heavy", 5)]

print("\n=== BẢNG TỔNG HỢP KẾT QUẢ MÔ PHỎNG TỪ NS-3 ===")
for sc_name, fig_num in scenarios:
    fig = plt.figure(figsize=(12, 8.5), dpi=300)
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 2, (3, 4))
    
    pos3 = ax3.get_position()
    new_w = pos3.width * 0.46
    ax3.set_position([pos3.x0 + (pos3.width - new_w) / 2.0, pos3.y0, new_w, pos3.height])

    print(f"\n--- Kịch bản: {sc_name} Traffic ---")
    print(f"{'Thuật toán':<10} | {'Peak Queue':<12} | {'Avg Queue (pkts)':<18} | {'Avg Delay (ms)':<16} | {'Throughput (Mbps)':<18}")
    print("-" * 82)

    for alg in ['RED', 'NLRED', 'SmRED', 'RED-QL']:
        q_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_queue.dat")
        d_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_delay.dat")
        t_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_tput.dat")

        if not os.path.exists(q_path):
            continue

        q_data = np.loadtxt(q_path)
        d_data = np.loadtxt(d_path)
        t_data = np.loadtxt(t_path)

        ax1.plot(q_data[:, 0], q_data[:, 1], label=alg, **styles[alg])
        ax2.plot(d_data[:, 0], d_data[:, 1], label=alg, **styles[alg])
        ax3.plot(t_data[:, 0], t_data[:, 1], label=alg, **styles[alg])

        print(f"{alg:<10} | {np.max(q_data[:, 1]):<12.2f} | {np.mean(q_data[:, 1]):<18.2f} | {np.mean(d_data[:, 1]):<16.2f} | {t_data[-1, 1]:<18.2f}")

    ax1.set_xlabel("Simulation Time (Seconds)\n(a)")
    ax1.set_ylabel("Average Queue Size (Packets)")
    ax1.set_xlim(0, 100)
    ax1.legend(loc='upper right', frameon=False)

    ax2.set_xlabel("Simulation Time (Seconds)\n(b)")
    ax2.set_ylabel("Delay (ms)")
    ax2.set_xlim(0, 100)
    ax2.legend(loc='lower right', frameon=False)

    ax3.set_xlabel("Simulation Time (Seconds)\n(c)")
    ax3.set_ylabel("Throughput (Mbps)")
    ax3.set_xlim(0, 100)
    ax3.legend(loc='lower right', frameon=False)

    out_fig = os.path.join(PLOTS_DIR, f"Figure_{fig_num}_{sc_name}_Traffic.png")
    plt.savefig(out_fig, bbox_inches='tight')
    plt.close()

print(f"\n-> Đã lưu toàn bộ 4 biểu đồ PNG tại: {PLOTS_DIR}")

import os
import numpy as np
import matplotlib.pyplot as plt

# Cấu hình font chữ to, rõ nét và hỗ trợ tiếng Việt
plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Liberation Sans'],
    'axes.unicode_minus': False,
    'font.size': 12,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 15
})

RESULTS_DIR = "scratch/red-ql-project/results/"
PLOTS_DIR = "scratch/red-ql-project/plots/"
os.makedirs(PLOTS_DIR, exist_ok=True)

# ==============================================================================
# 1. Vẽ Figure 1: Đường cong xác suất đánh rơi gói tin của RED-QL
# ==============================================================================
min_th, max_th, max_p = 30.0, 90.0, 0.1
target_ql = 2.0 * (max_th + min_th) / 3.0 - min_th

def pb_red_ql(ave):
    if ave < min_th:
        return 0.0
    elif ave < target_ql:
        return 9.0 * max_p * ((ave - min_th) / (2.0 * (max_th - 2.0 * min_th)))**2
    elif ave < max_th:
        return max_p + 3.0 * (1.0 - max_p) * ((ave - target_ql) / (max_th + min_th))
    else:
        return 1.0

ave_x = np.linspace(0, 100, 500)
pb_y = [pb_red_ql(x) for x in ave_x]

plt.figure(figsize=(8, 5.8), dpi=300)
plt.plot(ave_x, pb_y, color='#7a0019', linewidth=2.5, label='RED-QL')
plt.xlabel('Average Queue Size (Packets)')
plt.ylabel('Packet Dropping Probability')
plt.xlim(0, 100)
plt.ylim(0, 1.02)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='upper left', frameon=True, edgecolor='black')
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, "Figure_1_RED_QL_Curve.png"), dpi=300)
plt.close()

# ==============================================================================
# 2. Vẽ Figure 3, 4, 5 (Ảnh gộp 3-trong-1 VÀ 3 ảnh tách rời a, b, c)
# ==============================================================================
styles = {
    'RED':    {'color': '#d95f02', 'ls': ':',  'lw': 2.2},
    'NLRED':  {'color': '#000080', 'ls': '-.', 'lw': 2.2},
    'SmRED':  {'color': '#cc00cc', 'ls': '-',  'lw': 2.0},
    'RED-QL': {'color': '#000000', 'ls': '--', 'lw': 2.5}
}

scenarios = [
    ("Light", 3, "N = 5", "a"),
    ("Moderate", 4, "N = 20", "b"),
    ("Heavy", 5, "N = 50", "c")
]

full_table_rows = []
metrics_by_sc = {"Queue": [], "Delay": [], "Tput": []}

print("\n=== BẢNG TỔNG HỢP KẾT QUẢ MÔ PHỎNG TỪ NS-3 ===")
for sc_name, fig_num, n_label, sc_letter in scenarios:
    # Khởi tạo ảnh gộp 3 biểu đồ
    fig_comb = plt.figure(figsize=(14, 10), dpi=300)
    ax1 = fig_comb.add_subplot(2, 2, 1)
    ax2 = fig_comb.add_subplot(2, 2, 2)
    ax3 = fig_comb.add_subplot(2, 2, (3, 4))
    
    pos3 = ax3.get_position()
    new_w = pos3.width * 0.48
    ax3.set_position([pos3.x0 + (pos3.width - new_w) / 2.0, pos3.y0, new_w, pos3.height])

    # Khởi tạo 3 ảnh tách rời cho từng yếu tố (a), (b), (c)
    fig_a, ax_a = plt.subplots(figsize=(8.5, 5.8), dpi=300)
    fig_b, ax_b = plt.subplots(figsize=(8.5, 5.8), dpi=300)
    fig_c, ax_c = plt.subplots(figsize=(8.5, 5.8), dpi=300)

    print(f"\n--- Kịch bản: {sc_name} Traffic ---")
    print(f"{'Thuật toán':<10} | {'Peak Queue':<12} | {'Avg Queue (pkts)':<18} | {'Avg Delay (ms)':<16} | {'Throughput (Mbps)':<18}")
    print("-" * 82)

    sc_rows = []
    q_row = [f"{sc_name} ({n_label})"]
    d_row = [f"{sc_name} ({n_label})"]
    t_row = [f"{sc_name} ({n_label})"]

    for idx, alg in enumerate(['RED', 'NLRED', 'SmRED', 'RED-QL']):
        q_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_queue.dat")
        d_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_delay.dat")
        t_path = os.path.join(RESULTS_DIR, f"{alg}_{sc_name}_tput.dat")

        if not os.path.exists(q_path):
            continue

        q_data = np.loadtxt(q_path)
        d_data = np.loadtxt(d_path)
        t_data = np.loadtxt(t_path)

        # Vẽ trên ảnh gộp
        ax1.plot(q_data[:, 0], q_data[:, 1], label=alg, **styles[alg])
        ax2.plot(d_data[:, 0], d_data[:, 1], label=alg, **styles[alg])
        ax3.plot(t_data[:, 0], t_data[:, 1], label=alg, **styles[alg])

        # Vẽ trên 3 ảnh riêng biệt
        ax_a.plot(q_data[:, 0], q_data[:, 1], label=alg, **styles[alg])
        ax_b.plot(d_data[:, 0], d_data[:, 1], label=alg, **styles[alg])
        ax_c.plot(t_data[:, 0], t_data[:, 1], label=alg, **styles[alg])

        peak_q = np.max(q_data[:, 1])
        avg_q  = np.mean(q_data[:, 1])
        avg_d  = np.mean(d_data[:, 1])
        tput   = t_data[-1, 1]

        print(f"{alg:<10} | {peak_q:<12.2f} | {avg_q:<18.2f} | {avg_d:<16.2f} | {tput:<18.2f}")

        sc_col_text = f"{sc_name} Traffic\n({n_label})" if idx == 0 else ""
        full_table_rows.append([sc_col_text, alg, f"{peak_q:.2f}", f"{avg_q:.2f}", f"{avg_d:.2f}", f"{tput:.2f}"])
        sc_rows.append([alg, f"{peak_q:.2f}", f"{avg_q:.2f}", f"{avg_d:.2f}", f"{tput:.2f}"])
        q_row.append(f"{avg_q:.2f}")
        d_row.append(f"{avg_d:.2f}")
        t_row.append(f"{tput:.2f}")

    if len(q_row) == 5:
        metrics_by_sc["Queue"].append(q_row)
        metrics_by_sc["Delay"].append(d_row)
        metrics_by_sc["Tput"].append(t_row)

    # Xuất ảnh bảng số liệu riêng cho từng kịch bản tải
    if len(sc_rows) > 0:
        cols_sc = ["Thuật toán", "Peak Queue\n(packets)", "Avg Queue\n(packets)", "Avg Delay\n(ms)", "Throughput\n(Mbps)"]
        fig_s, ax_s = plt.subplots(figsize=(9.0, 3.4), dpi=300)
        ax_s.axis('off')
        ax_s.set_title(f"Kết quả mô phỏng kịch bản {sc_name} Traffic ({n_label})", fontsize=13, fontweight='bold', pad=12)
        t_s = ax_s.table(cellText=sc_rows, colLabels=cols_sc, cellLoc='center', loc='center', colWidths=[0.2]*5)
        t_s.auto_set_font_size(False)
        t_s.set_fontsize(11)
        t_s.scale(1.0, 1.75)
        for (r, c), cell in t_s.get_celld().items():
            cell.set_edgecolor('#333333')
            cell.set_linewidth(0.9)
            if r == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#1b365d')
            else:
                alg_n = sc_rows[r - 1][0]
                if alg_n == "RED-QL":
                    cell.set_facecolor('#fff2cc')
                    cell.set_text_props(weight='bold', color='#b22222')
                elif r % 2 == 0:
                    cell.set_facecolor('#f4f7fa')
                else:
                    cell.set_facecolor('#ffffff')
                if c == 0 and alg_n != "RED-QL":
                    cell.set_text_props(weight='bold', color='#1b365d')
        fig_s.tight_layout()
        fig_s.savefig(os.path.join(PLOTS_DIR, f"Bang_5_5{sc_letter}_{sc_name}_Traffic.png"), bbox_inches='tight', dpi=300)
        plt.close(fig_s)

    # Lưu ảnh biểu đồ gộp
    for ax, ylabel, sub_label, leg_loc in [
        (ax1, "Average Queue Size (Packets)", "(a)", "upper right"),
        (ax2, "Delay (ms)", "(b)", "upper right"),
        (ax3, "Throughput (Mbps)", "(c)", "lower right")
    ]:
        ax.set_xlabel(f"Simulation Time (Seconds)\n{sub_label}")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 100)
        ax.grid(True, linestyle='--', alpha=0.45)
        ax.legend(loc=leg_loc, frameon=True, edgecolor='black', facecolor='white', framealpha=0.9)

    fig_comb.savefig(os.path.join(PLOTS_DIR, f"Figure_{fig_num}_{sc_name}_Traffic.png"), bbox_inches='tight', dpi=300)
    plt.close(fig_comb)

    # Lưu 3 ảnh biểu đồ tách rời (a, b, c)
    for fig_sep, ax_sep, ylabel, sub_label, suffix, leg_loc in [
        (fig_a, ax_a, "Average Queue Size (Packets)", "(a)", "a_Queue", "upper right"),
        (fig_b, ax_b, "Delay (ms)", "(b)", "b_Delay", "upper right"),
        (fig_c, ax_c, "Throughput (Mbps)", "(c)", "c_Throughput", "lower right")
    ]:
        ax_sep.set_xlabel(f"Simulation Time (Seconds)\n{sub_label}")
        ax_sep.set_ylabel(ylabel)
        ax_sep.set_xlim(0, 100)
        ax_sep.grid(True, linestyle='--', alpha=0.45)
        ax_sep.legend(loc=leg_loc, frameon=True, edgecolor='black', facecolor='white', framealpha=0.9)
        fig_sep.tight_layout()
        fig_sep.savefig(os.path.join(PLOTS_DIR, f"Figure_{fig_num}{suffix}_{sc_name}.png"), bbox_inches='tight', dpi=300)
        plt.close(fig_sep)

# ==============================================================================
# 3. Vẽ ảnh Bảng 5.5 tổng hợp chung và Bảng 1, 2, 3 theo từng chỉ số
# ==============================================================================
if len(full_table_rows) > 0:
    cols_full = ["Kịch bản tải", "Thuật toán", "Peak Queue\n(packets)", "Avg Queue\n(packets)", "Avg Delay\n(ms)", "Throughput\n(Mbps)"]
    fig_tbl, ax_tbl = plt.subplots(figsize=(11, 6.5), dpi=300)
    ax_tbl.axis('off')
    ax_tbl.set_title("Bảng 5.5: Tổng hợp các số liệu thực tế kết quả chạy mô phỏng trên ns-3", fontsize=14, fontweight='bold', pad=18)
    table = ax_tbl.table(cellText=full_table_rows, colLabels=cols_full, cellLoc='center', loc='center', colWidths=[0.23, 0.13, 0.16, 0.16, 0.16, 0.16])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 1.7)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#333333')
        cell.set_linewidth(0.9)
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#1b365d')
            cell.set_height(0.11)
        else:
            if full_table_rows[row - 1][1] == "RED-QL":
                cell.set_facecolor('#fff2cc')
                cell.set_text_props(weight='bold', color='#b22222')
            elif ((row - 1) // 4) % 2 == 1:
                cell.set_facecolor('#f4f7fa')
            else:
                cell.set_facecolor('white')
            if col == 0 and full_table_rows[row - 1][0] != "":
                cell.set_text_props(weight='bold', color='#1b365d')
    fig_tbl.tight_layout()
    fig_tbl.savefig(os.path.join(PLOTS_DIR, "Bang_5_5_Tong_Hop_Chung.png"), bbox_inches='tight', dpi=300)
    plt.close(fig_tbl)

def save_metric_table(title, rows_data, fname):
    if len(rows_data) == 0:
        return
    fig, ax = plt.subplots(figsize=(8.5, 3.2), dpi=300)
    ax.axis('off')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    t = ax.table(cellText=rows_data, colLabels=["Kịch bản tải", "RED", "NLRED", "SmRED", "RED-QL"],
                 cellLoc='center', loc='center', colWidths=[0.28, 0.18, 0.18, 0.18, 0.18])
    t.auto_set_font_size(False)
    t.set_fontsize(11.5)
    t.scale(1.0, 1.8)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor('#333333')
        cell.set_linewidth(0.9)
        if r == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#1b365d')
        else:
            cell.set_facecolor('#f4f7fa' if r % 2 == 0 else '#ffffff')
            if c == 0:
                cell.set_text_props(weight='bold', color='#1b365d')
            if c == 4:
                cell.set_facecolor('#fff2cc')
                cell.set_text_props(weight='bold', color='#b22222')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, fname), bbox_inches='tight', dpi=300)
    plt.close()

save_metric_table("Bảng 1: So sánh kích thước hàng đợi trung bình - Average Queue Size (packets)", metrics_by_sc["Queue"], "Bang_1_Average_Queue_Size.png")
save_metric_table("Bảng 2: So sánh độ trễ hàng đợi trung bình - Average Delay (ms)", metrics_by_sc["Delay"], "Bang_2_Average_Delay.png")
save_metric_table("Bảng 3: So sánh thông lượng trung bình - Throughput (Mbps)", metrics_by_sc["Tput"], "Bang_3_Throughput.png")

print(f"\n-> Đã xuất toàn bộ biểu đồ và các bảng số liệu tại: {PLOTS_DIR}")

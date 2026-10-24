#!/bin/bash

echo "=== Đang cấu hình và biên dịch ns-3 ==="
./ns3 configure --enable-examples --enable-tests
./ns3 build red-ql-sim

SCENARIOS=("Light:5" "Moderate:20" "Heavy:50")
ALGS=("RED:0" "NLRED:1" "SmRED:2" "RED-QL:3")

echo "=== BẮT ĐẦU CHẠY 12 KỊCH BẢN MÔ PHỎNG ==="

for sc in "${SCENARIOS[@]}"; do
    SC_NAME="${sc%%:*}"
    N_SENDERS="${sc##*:}"
    for alg in "${ALGS[@]}"; do
        ALG_NAME="${alg%%:*}"
        ALG_ID="${alg##*:}"
        PREFIX="${ALG_NAME}_${SC_NAME}"
        
        echo "-> Kịch bản: ${SC_NAME} (N=${N_SENDERS}) | Thuật toán: ${ALG_NAME}..."
        ./ns3 run "red-ql-sim --nSenders=${N_SENDERS} --aqmVariant=${ALG_ID} --prefix=${PREFIX}" --no-build
    done
done

echo "=== HOÀN TẤT! Đang vẽ biểu đồ kết quả ==="
python3 scratch/red-ql-project/plot_results.py

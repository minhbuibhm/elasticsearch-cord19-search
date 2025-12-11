import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CHUẨN BỊ DỮ LIỆU 
# ---------------------------------------------------------
data = {
    "Method": ["BM25 (Lexical)", "SciBERT (Semantic)", "Hybrid (RRF)"],
    "Avg Latency (ms)": [6.38, 26.06, 43.53],
    "P99 Latency (ms)": [10.10, 57.41, 82.58]
}

df = pd.DataFrame(data)

# Thiết lập style cho biểu đồ (Seaborn style)
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif'})

# ---------------------------------------------------------
# 2. VẼ BIỂU ĐỒ SO SÁNH ĐỘ TRỄ (AVG LATENCY)
# ---------------------------------------------------------
def plot_avg_latency():
    plt.figure(figsize=(10, 6))
    
    # Tạo Bar Plot
    ax = sns.barplot(
        x="Method", 
        y="Avg Latency (ms)", 
        data=df, 
        palette=["#6c757d", "#0d6efd", "#ffc107"], # Xám, Xanh, Vàng
        edgecolor="black"
    )

    # Thêm tiêu đề và nhãn
    plt.title("So sánh Độ trễ Trung bình (Average Latency)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Phương pháp tìm kiếm", fontsize=13)
    plt.ylabel("Thời gian (ms)", fontsize=13)
    plt.ylim(0, 60) # Giới hạn trục Y để biểu đồ thoáng hơn

    # Thêm giá trị số lên đầu mỗi cột
    for i, v in enumerate(df["Avg Latency (ms)"]):
        ax.text(i, v + 1, f"{v} ms", ha='center', va='bottom', fontsize=14, fontweight='bold')

    # Lưu và hiển thị
    plt.tight_layout()
    plt.savefig("chart_avg_latency.png", dpi=300)
    print("✅ Đã lưu biểu đồ: chart_avg_latency.png")
    plt.show()

# ---------------------------------------------------------
# 3. VẼ BIỂU ĐỒ ĐA CHIỀU (AVG vs P99)
# ---------------------------------------------------------
def plot_grouped_comparison():
    # Chuyển đổi dữ liệu sang dạng "long format" để vẽ Grouped Bar Chart
    df_melted = df.melt(id_vars="Method", var_name="Metric", value_name="Latency")
    
    plt.figure(figsize=(12, 7))
    
    ax = sns.barplot(
        x="Method", 
        y="Latency", 
        hue="Metric", 
        data=df_melted,
        palette="viridis",
        edgecolor="black"
    )

    plt.title("Hiệu năng & Độ ổn định (Avg vs P99)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("", fontsize=12)
    plt.ylabel("Thời gian phản hồi (ms)", fontsize=13)
    plt.legend(title="Chỉ số")

    # Thêm giá trị
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f ms', padding=3, fontsize=11)

    plt.tight_layout()
    plt.savefig("chart_performance_comparison.png", dpi=300)
    print("✅ Đã lưu biểu đồ: chart_performance_comparison.png")
    plt.show()

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🎨 Đang vẽ biểu đồ...")
    plot_avg_latency()
    plot_grouped_comparison()
    print("Hoàn tất!")
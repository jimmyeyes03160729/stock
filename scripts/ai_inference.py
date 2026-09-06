import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yfinance as yf

# 1. 依論文定義 CNN_5_model 架構 (圖片三)
class CNN_5_model(nn.Module):
    def __init__(self, in_features=15360, num_classes=2):
        super(CNN_5_model, self).__init__()
        self.conv1 = nn.Conv2d(1, 64, kernel_size=(5, 3), stride=(1, 1), padding=(2, 1))
        self.bn1 = nn.BatchNorm2d(64, eps=1e-05, momentum=0.1)
        self.relu1 = nn.LeakyReLU(negative_slope=0.01)
        self.pool1 = nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1))

        self.conv2 = nn.Conv2d(64, 128, kernel_size=(5, 3), stride=(1, 1), padding=(2, 1))
        self.bn2 = nn.BatchNorm2d(128, eps=1e-05, momentum=0.1)
        self.relu2 = nn.LeakyReLU(negative_slope=0.01)
        self.pool2 = nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1))

        self.dropout = nn.Dropout(p=0.5)
        self.fc = nn.Linear(in_features=in_features, out_features=num_classes)

    def forward(self, x):
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.fc(x)
        return x

# 2. 將 5 日資料轉成 0/1 像素線圖 (圖片一標準化實作)
def ohlcv_to_pixel_image(df_window, img_height=60, img_width=30):
    img = np.zeros((img_height, img_width), dtype=np.float32)
    p_height = int(img_height * 0.75)
    v_height = img_height - p_height

    p_min = df_window[["Open", "High", "Low", "Close"]].values.min()
    p_max = df_window[["Open", "High", "Low", "Close"]].values.max()
    p_range = p_max - p_min if p_max > p_min else 1e-5

    n_days = len(df_window)
    col_step = img_width // n_days

    for i in range(n_days):
        row = df_window.iloc[i]
        c_x = i * col_step + (col_step // 2)

        y_open = int((1.0 - (row["Open"] - p_min) / p_range) * (p_height - 1))
        y_close = int((1.0 - (row["Close"] - p_min) / p_range) * (p_height - 1))
        y_high = int((1.0 - (row["High"] - p_min) / p_range) * (p_height - 1))
        y_low = int((1.0 - (row["Low"] - p_min) / p_range) * (p_height - 1))

        # 畫影線與實體線 (值為 1)
        img[min(y_high, y_low):max(y_high, y_low)+1, c_x] = 1.0
        x_left = max(0, c_x - 1)
        x_right = min(img_width, c_x + 2)
        img[min(y_open, y_close):max(y_open, y_close)+1, x_left:x_right] = 1.0

        # 成交量
        v_max = df_window["Volume"].max()
        v_range = v_max if v_max > 0 else 1.0
        vol = row["Volume"]
        v_bar_h = int((vol / v_range) * (v_height - 1))
        img[img_height - v_bar_h:img_height, c_x] = 1.0

    return img

# 3. 主執行流程
def main():
    target_stocks = ["2330", "2317", "2454", "2457", "6862", "2603", "2382", "3231", "3037", "00878", "0050"]
    os.makedirs("public/data", exist_ok=True)
    
    device = torch.device("cpu")
    model = CNN_5_model()
    # 若有預訓練權重可載入：
    # if os.path.exists("models/best_cnn5_model.pt"):
    #     model.load_state_dict(torch.load("models/best_cnn5_model.pt", map_location=device))
    model.eval()

    results = []

    for sym in target_stocks:
        ticker = f"{sym}.TW"
        df = yf.download(ticker, period="1mo", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        if len(df) < 5:
            continue

        df_last5 = df.tail(5)
        current_price = float(df_last5["Close"].iloc[-1])
        img_array = ohlcv_to_pixel_image(df_last5)

        # 轉成 PyTorch Tensor
        img_tensor = torch.tensor(img_array).unsqueeze(0).unsqueeze(0).to(device) # (1, 1, 60, 30)

        with torch.no_grad():
            # 推論預測
            logits = model(img_tensor)
            probs = torch.softmax(logits, dim=1)
            prob_up = float(probs[0][1].item())
            prob_down = float(probs[0][0].item())

        # 判定建議 (Decile 排序標籤)
        if prob_up >= 0.65:
            action = "強烈建議買"
            badge_color = "red"
        elif prob_down >= 0.65:
            action = "弱勢建議空"
            badge_color = "emerald"
        else:
            action = "中立觀望"
            badge_color = "slate"

        results.append({
            "symbol": sym,
            "current_price": round(current_price, 2),
            "prob_up": round(prob_up * 100, 1),
            "prob_down": round(prob_down * 100, 1),
            "action": action,
            "badge_color": badge_color,
            "image_matrix": img_array.tolist() # 傳給前端可直接還原這張黑白影像
        })

    # 依照上漲機率排序
    results.sort(key=lambda x: x["prob_up"], reverse=True)

    output_payload = {
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_type": "CNN_5_model (I5/R5 五日圖像化預測)",
        "stocks": results
    }

    with open("public/data/ai_signals.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)
    print("AI 預測訊號產生完成！")

if __name__ == "__main__":
    main()

# Máy soi văn AI

Chương trình kiểm tra một đoạn văn (tiếng Việt hoặc tiếng Anh) do AI hay người viết. Nó chạy hoàn toàn trên máy bạn, không gửi văn bản đi đâu, và có cả dòng lệnh lẫn giao diện web.

Kết quả là **xác suất**, không phải bằng chứng. Hãy dùng nó để tìm chỗ văn nghe máy móc rồi sửa, đừng dùng để kết tội ai.

## Chương trình chấm như thế nào

Điểm cuối cùng gộp hai phần, mô hình chiếm 70%:

1. **Mô hình ngôn ngữ, theo phương pháp Binoculars** (Hans và cộng sự, 2024). Hai mô hình Qwen2.5 (bản base và bản instruct) cùng đọc văn bản:
   - *log-perplexity*: từng chữ có dễ đoán với mô hình không. Văn AI thường rất dễ đoán.
   - *cross-perplexity*: mức dễ đoán mà mô hình "kỳ vọng" ở vị trí đó.
   - **Điểm Binoculars = log-perplexity ÷ cross-perplexity.** Điểm thấp hơn ngưỡng nghĩa là giống AI. Phép chia giúp không chấm nhầm những đề tài vốn dễ đoán như văn mẫu.
   - Mỗi câu cũng được chấm riêng, nên bạn thấy câu nào bị nghi nhất.
2. **Sáu dấu hiệu văn phong** (không cần mô hình): câu dài đều nhau, cụm từ sáo rỗng ("hành trình", "đóng vai trò quan trọng"), từ nối đầu câu ("Bên cạnh đó", "Hơn nữa"), thiếu giọng nói thật (nhé, á, thôi, mình), lặp từ vựng, lặp cụm 3 chữ.

## Cài đặt

Cần Python 3.10 trở lên.

```bash
git clone https://github.com/kipoikibo995-sys/checkai
cd checkai
pip install -r requirements.txt
```

Lần chạy đầu tiên chương trình sẽ tự tải mô hình từ Hugging Face (preset `nhe` khoảng 2 GB). Những lần sau dùng lại bản đã tải.

Không muốn cài mô hình? Thêm `--no-model` vào mọi lệnh. Khi đó chương trình chỉ dùng sáu dấu hiệu văn phong, chạy ngay mà không cần cài gì thêm.

## Sử dụng

**Giao diện web** (dễ nhất):

```bash
python -m aicheck serve
```

Sau đó mở http://127.0.0.1:8000, dán văn bản và bấm Kiểm tra (hoặc Ctrl+Enter).

**Dòng lệnh:**

```bash
python -m aicheck check samples/mau-ai.txt          # một tệp
python -m aicheck check bai-viet/                   # cả thư mục .txt
python -m aicheck check bai.txt --json > ketqua.json
echo "Dán văn bản ở đây..." | python -m aicheck check
```

**Chọn mô hình:**

| Lựa chọn | Mô hình | Cần |
|---|---|---|
| `--preset nhe` (mặc định) | Qwen2.5-0.5B + Instruct | khoảng 4 GB RAM, chạy được trên CPU |
| `--preset chuan` | Qwen2.5-1.5B + Instruct | khoảng 12 GB RAM, hoặc GPU 8 GB |
| `--preset manh` | Qwen2.5-7B + Instruct | GPU từ 24 GB |
| `--single` | chỉ dùng mô hình base | tốn một nửa bộ nhớ, kém chính xác hơn |

Có thể chỉ định mô hình khác bằng `--observer` và `--performer`, miễn là hai mô hình cùng họ (chung bộ từ vựng).

## Hiệu chỉnh (nên làm)

Ngưỡng mặc định 0,90 lấy từ bài báo gốc, vốn dùng mô hình khác, nên với Qwen nó có thể lệch. Để chương trình chính xác với loại văn bạn hay kiểm tra, hãy hiệu chỉnh bằng văn mẫu của chính bạn:

1. Tạo thư mục `mau/nguoi/` chứa các tệp `.txt` bạn chắc chắn do người viết, ví dụ bài cũ trước năm 2022.
2. Tạo thư mục `mau/ai/` chứa các tệp `.txt` do ChatGPT, Claude, Gemini… viết về cùng chủ đề.
3. Nên có từ 20 tệp mỗi loại, mỗi tệp trên 150 chữ. Rồi chạy:

```bash
python -m aicheck calibrate --human mau/nguoi --ai mau/ai
```

Chương trình in ra ngưỡng mới cùng độ chính xác trên mẫu, rồi lưu vào `~/.aicheck/calibration.json`. Mọi lần kiểm tra sau với cùng cặp mô hình sẽ tự dùng ngưỡng này.

## Giới hạn cần biết

- Đoạn văn dưới khoảng 120 chữ cho kết quả rất không chắc chắn.
- Văn viết theo khuôn (báo cáo, văn mẫu, bài SEO) dễ bị chấm nhầm là AI.
- Văn AI đã được người sửa nhiều, hoặc nhờ AI viết lại vài lượt, sẽ khó phát hiện.
- Không có công cụ nào, kể cả GPTZero hay Turnitin, đúng 100%.

## Bản chạy trên trình duyệt

`browser/index.html` là bản rút gọn chỉ dùng sáu dấu hiệu văn phong, không cần cài gì: mở thẳng tệp bằng trình duyệt, hoặc bật GitHub Pages cho repo để có đường link chia sẻ.

## Cấu trúc thư mục

```
aicheck/heuristics.py   sáu dấu hiệu văn phong
aicheck/model.py        chấm Binoculars bằng mô hình ngôn ngữ
aicheck/detector.py     gộp điểm, kết luận, hiệu chỉnh ngưỡng
aicheck/server.py       máy chủ web (thư viện chuẩn)
aicheck/web.html        giao diện web
aicheck/__main__.py     dòng lệnh
samples/                hai đoạn văn mẫu
browser/index.html      bản trình duyệt, không cần Python
tests/                  kiểm thử: python -m unittest discover -s tests
```

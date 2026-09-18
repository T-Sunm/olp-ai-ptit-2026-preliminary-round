# HỎI ĐÁP TRÊN ẢNH TÀI LIỆU

## 1. Mô tả bài toán

Một câu hỏi về tài liệu hành chính hiếm khi được trả lời bằng cách tra một từ khóa. *"Tổng chỉ tiêu tuyển mới của hai phòng ban có định biên 30 là bao nhiêu?"* — con số ấy không được in ở bất kỳ đâu trên trang giấy. Nó chỉ xuất hiện sau khi tìm đúng vài ô trong một bảng, hiểu được quan hệ hàng và cột giữa chúng, rồi cộng lại.

Trả lời đúng vẫn chưa đủ nếu hệ thống không nói được nó lấy số từ đâu. Người kiểm tra cần nhìn thấy chính xác vùng nào trên trang nào đã dẫn tới đáp án; nếu không, không có cách nào phân biệt một suy luận đúng với một phỏng đoán may mắn.

Trong tác vụ **Hỏi đáp trên ảnh tài liệu**, mỗi mẫu dữ liệu gồm ảnh trang tài liệu, kết quả OCR kèm tọa độ của từng khối văn bản, và các câu hỏi tiếng Việt về nội dung tài liệu đó. Với mỗi câu hỏi, các đội thi cần đưa ra câu trả lời dạng văn bản và danh sách vùng bằng chứng trên trang. Cả hai phần đều được tính điểm.

## 2. Mô tả dữ liệu

Dữ liệu được chia thành ba tập:

| Tập dữ liệuSố tài liệuSố ảnh trangSố câu hỏiNhãnMục đích |       |       |        |               |                                     |
| -------------------------------------------------------- | ----- | ----- | ------ | ------------- | ----------------------------------- |
| `training_set`                                           | 1.100 | 1.426 | 11.000 | Có            | Huấn luyện và kiểm tra chương trình |
| `public_test`                                            | 100   | 131   | 1.000  | Không công bố | Đánh giá công khai                  |
| `private_test`                                           | 200   | 265   | 2.000  | Không công bố | Đánh giá và xếp hạng cuối cùng      |

Mỗi tài liệu gồm một hoặc hai trang và có đúng 10 câu hỏi. Ảnh trang là JPEG khổ dọc, độ phân giải thay đổi theo tài liệu, nằm trong khoảng từ 1600×2263 đến 2000×2828 pixel. Đáp án chia thành hai loại: chuỗi văn bản lấy từ nội dung tài liệu và giá trị số tính ra từ bảng.

Câu hỏi được sinh theo tám kiểu suy luận, phân bố trong tập huấn luyện như sau:

| Kiểu suy luậnSố câu hỏiYêu cầu |       |                                              |
| ------------------------------ | ----- | -------------------------------------------- |
| `lookup`                       | 2.200 | Tra trực tiếp giá trị của một ô              |
| `argmax`                       | 1.898 | Tìm dòng có giá trị lớn nhất                 |
| `argmin`                       | 1.874 | Tìm dòng có giá trị nhỏ nhất                 |
| `sum`                          | 1.810 | Cộng giá trị của nhiều ô                     |
| `compare`                      | 1.722 | So sánh hai giá trị                          |
| `count`                        | 915   | Đếm số dòng thỏa điều kiện                   |
| `visual_bold_lookup`           | 535   | Tra ô được in đậm, chỉ nhận biết được từ ảnh |
| `cross_page_sum`               | 46    | Cộng giá trị nằm trên hai trang khác nhau    |

Dữ liệu nằm tại `/home/user/TACVU2`:

```text
TACVU2/
|-- baseline_TACVU2.ipynb           # Code mẫu tham khảo
|-- data/
    |-- training_set/
    |   |-- manifest.jsonl          # Thông tin 1.100 tài liệu
    |   |-- questions.jsonl         # 11.000 câu hỏi
    |   |-- labels.jsonl            # Đáp án và vùng bằng chứng
    |   |-- cell_annotations.jsonl  # Chú giải từng ô bảng
    |   |-- images/                 # 1.426 ảnh trang
    |   |-- ocr/                    # 1.100 tệp OCR
    |-- public_test/
    |   |-- manifest.jsonl          # Thông tin 100 tài liệu
    |   |-- questions.jsonl         # 1.000 câu hỏi
    |   |-- images/                 # 131 ảnh trang
    |   |-- ocr/                    # 100 tệp OCR
    |-- private_test.zip            # Được bảo vệ bằng mật khẩu

```

`private_test.zip` **chỉ được công bố mật khẩu khi bắt đầu Giai đoạn kiểm tra bí mật**. Sau khi giải nén, tập private test có cấu trúc giống hệt `public_test`.

### Tệp manifest.jsonl

Mỗi dòng mô tả một tài liệu:

```json
{"id": "B-public-00000", "image_paths": ["images/B-public-00000_p01.jpg"], "ocr_path": "ocr/B-public-00000.json", "page_count": 1, "question_count": 10, "split": "public_test"}

```

Đường dẫn trong `image_paths` và `ocr_path` là đường dẫn **tương đối so với thư mục của tập dữ liệu**.

### Tệp questions.jsonl

Mỗi dòng là một câu hỏi:

```json
{"question_id": "B-train-00000-q01", "document_id": "B-train-00000", "question": "Trong bảng 1 ở trang 1, tổng Tuyển mới của hai dòng có Phòng ban “Chăm sóc khách hàng” và Phòng ban “Kế toán” và Định biên “30” là bao nhiêu?"}

```

### Tệp ocr/\*.json

Mỗi tài liệu có một tệp OCR, chứa kích thước từng trang và danh sách khối văn bản kèm tọa độ:

```json
{
  "coordinate_system": "normalized_xyxy",
  "document_id": "B-train-00000",
  "pages": [
    {
      "page": 1,
      "width": 1600,
      "height": 2263,
      "blocks": [
        {"block_id": "p01_b00000", "page": 1, "text": "Phòng ban", "bbox": [0.0525, 0.209456, 0.304375, 0.235086]}
      ]
    }
  ]
}

```

Tọa độ `bbox` ở dạng chuẩn hóa `[x1, y1, x2, y2]`: mọi giá trị thuộc đoạn `[0, 1]`, gốc tọa độ nằm ở góc trên bên trái của trang, và luôn thỏa mãn `x1 < x2`, `y1 < y2`.

### Nhãn của tập huấn luyện

`labels.jsonl` chứa 11.000 dòng, mỗi dòng ứng với một câu hỏi:

```json
{"question_id": "B-train-00000-q01", "answers": ["7"], "answer_type": "number", "reasoning_type": "sum", "evidence": [{"page": 1, "block_id": "p01_b00030", "bbox": [0.0525, 0.34114, 0.304375, 0.362351]}]}

```

- `answers`: danh sách các cách viết đáp án được chấp nhận.
- `answer_type`: `text` hoặc `number`.
- `reasoning_type`: kiểu suy luận của câu hỏi.
- `evidence`: các vùng trên trang dẫn tới đáp án; mỗi vùng gồm `page`, `bbox` và `block_id` tương ứng trong tệp OCR. Một câu hỏi thường có từ 2 đến 6 vùng bằng chứng.

`cell_annotations.jsonl` chứa 256.040 dòng, mỗi dòng là một ô bảng đã được chú giải: `document_id`, `page`, `table`, `row`, `column`, `block_id`, `bbox`, `clean_text`, `is_bold` và `is_header`.

Hai tệp `labels.jsonl` và `cell_annotations.jsonl` chỉ có trong `training_set`.

## 3. Cấu trúc file nộp

Các đội thi cần nộp **01 file ZIP** có cấu trúc:

```text
submission.zip
|-- predictions.jsonl

```

Trình chấm tìm `predictions.jsonl` ở bất kỳ vị trí nào trong ZIP và bỏ qua mọi tệp khác, nên nộp kèm notebook hay mã nguồn cũng không sao. Điều bắt buộc là **tên tệp phải đúng \*\*\*\*\*\*\*\*\*\*\*\*****`predictions.jsonl`**.

Mỗi dòng là một JSON object gồm đúng ba trường:

```json
{"question_id":"B-public-00000-q01","answer":"7","evidence":[{"page":1,"bbox":[0.10,0.20,0.30,0.40]}]}

```

Trong đó:

- `question_id`: mã câu hỏi trong `questions.jsonl`.
- `answer`: câu trả lời dạng chuỗi không rỗng.
- `evidence`: danh sách các vùng bằng chứng; mỗi phần tử chỉ gồm `page` và `bbox`.
- `page`: số nguyên dương chỉ trang chứa bằng chứng.
- `bbox`: vùng bằng chứng theo hệ tọa độ chuẩn hóa.

Mỗi `question_id` phải xuất hiện đúng một lần. Danh sách mã câu hỏi phải khớp hoàn toàn với tập kiểm tra của giai đoạn hiện tại. Bài nộp có thể không được chấm nếu thiếu hoặc thừa câu hỏi, trùng mã, hoặc có trường không hợp lệ.

## 4. Thang đo đánh giá

Điểm của mỗi câu hỏi được tính theo công thức:

```math
Question_Score=0,85×ANLS+0,15×Evidence-F1
```

Trong đó:

- `ANLS` đánh giá mức độ tương đồng giữa câu trả lời dự đoán và câu trả lời chuẩn.
- `Evidence-F1` đánh giá mức độ khớp của các vùng bằng chứng; một cặp vùng trên cùng trang được coi là khớp khi `IoU >= 0,5`.

Điểm của bài nộp là trung bình điểm của toàn bộ câu hỏi, quy đổi về thang 100:

```math
Score=100×1N∑i=1NQuestion_Scorei
```

Điểm hiển thị trên bảng xếp hạng được chuẩn hoá từ `Score` theo công thức:

```math
Final_Score={100×Score−MinMax−Min,neˆˊu Score>Min0,neˆˊu Score≤Min
```

Trong đó:

- `Min`: ngưỡng tối thiểu do Ban tổ chức quy định cho tác vụ.
- `Max`: điểm cao nhất hiện có trên bảng xếp hạng của tác vụ.

Mỗi khi `Max` thay đổi, điểm chuẩn hoá của toàn bộ đội thi được tính lại theo công thức trên.

Kết quả trên `public_test` được dùng để phản hồi trong thời gian thi; thứ hạng cuối cùng được xác định bằng `private_test`.

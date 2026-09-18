# TRÍCH XUẤT BẢNG TỪ ẢNH TÀI LIỆU

## 1. Mô tả bài toán

Phần lớn thông tin có giá trị trong tài liệu hành chính nằm trong bảng: bảng lương, biểu thống kê, danh mục hàng hóa, báo cáo doanh thu theo khu vực. Khi tài liệu chỉ còn tồn tại dưới dạng ảnh chụp hoặc bản scan, cấu trúc đó biến mất — máy chỉ nhìn thấy những nét mực trên nền giấy. Muốn tra cứu, tổng hợp hay đưa số liệu vào hệ thống, trước hết phải dựng lại được đúng cái bảng ban đầu.

Khó khăn không nằm ở việc đọc chữ. Một bảng có thể không kẻ viền, tiêu đề gộp ngang nhiều cột, ô dữ liệu kéo dọc qua nhiều hàng, nội dung xuống dòng ngay bên trong một ô, hoặc chạy dài sang trang thứ hai. Chỉ cần nhận nhầm một ranh giới cột, mọi ô phía sau đều lệch theo và cả bảng trở nên vô nghĩa.

Trong tác vụ **Trích xuất bảng**, mỗi mẫu dữ liệu là một tài liệu gồm một đến hai ảnh trang A4 chứa một hoặc nhiều bảng. Các đội thi cần chuyển toàn bộ bảng trong tài liệu sang định dạng Markdown mở rộng, bảo toàn thứ tự bảng, nội dung văn bản, số hàng và số cột, ô gộp, ngắt dòng trong ô và các đoạn chữ in đậm. Kết quả của mỗi tài liệu được lưu thành một tệp Markdown riêng, tên tệp trùng với `id` của tài liệu trong `manifest.jsonl`.

## 2. Mô tả dữ liệu

Dữ liệu được chia thành ba tập:

| Tập dữ liệuSố tài liệuSố ảnh trangNhãnMục đích |       |       |               |                                     |
| ---------------------------------------------- | ----- | ----- | ------------- | ----------------------------------- |
| `training_set`                                 | 1.100 | 1.375 | Có            | Huấn luyện và kiểm tra chương trình |
| `public_test`                                  | 50    | 52    | Không công bố | Đánh giá công khai                  |
| `private_test`                                 | 80    | 86    | Không công bố | Đánh giá và xếp hạng cuối cùng      |

Mỗi tài liệu gồm một hoặc hai trang. Ảnh trang là JPEG khổ dọc, độ phân giải thay đổi theo tài liệu, nằm trong khoảng từ 1600×2263 đến 2000×2828 pixel.

Tập huấn luyện được gán bốn mức độ khó tăng dần qua trường `difficulty`:

| MứcSố tài liệuĐặc điểm |     |                                                                                                                  |
| ---------------------- | --- | ---------------------------------------------------------------------------------------------------------------- |
| `M1`                   | 325 | Một bảng kẻ viền đầy đủ, một trang, tối đa 7 cột, không có ô gộp                                                 |
| `M2`                   | 330 | Kẻ viền đầy đủ, tối đa 9 cột, có ô gộp và ô nhiều dòng, một số tài liệu hai trang                                |
| `M3`                   | 280 | Tối đa 12 cột, tối đa 3 bảng, xuất hiện bảng kẻ viền một phần hoặc không kẻ viền, có ký tự `\|` trong nội dung ô |
| `M4`                   | 165 | Tối đa 14 cột, đa số hai trang, bảng dài vắt qua trang, không có bảng nào kẻ viền đầy đủ                         |

Hai tập kiểm tra chỉ gồm tài liệu mức `M1` và `M2`, và không kèm trường `difficulty` trong `manifest.jsonl`. Kết quả chấm được trả về kèm điểm tách riêng theo từng mức.

Dữ liệu nằm tại `/home/user/TACVU2`:

```text
TACVU2/
|-- baseline_TACVU2.ipynb           # Code mẫu tham khảo
|-- data/
    |-- training_set/
    |   |-- manifest.jsonl          # Thông tin 1.100 tài liệu
    |   |-- images/                 # 1.375 ảnh trang
    |   |-- labels/                 # Nhãn Markdown của cả tài liệu
    |   |-- page_labels/            # Nhãn Markdown tách theo từng trang
    |-- public_test/
    |   |-- manifest.jsonl          # Thông tin 50 tài liệu
    |   |-- images/                 # 52 ảnh trang
    |-- private_test.zip            # Được bảo vệ bằng mật khẩu
```

`private_test.zip` **chỉ được công bố mật khẩu khi bắt đầu Giai đoạn kiểm tra bí mật**. Sau khi giải nén, tập private test có cấu trúc giống hệt `public_test`.

### Tệp manifest.jsonl

Mỗi dòng là một JSON object mô tả một tài liệu:

```json
{"id": "public_test-00000", "image_paths": ["images/public_test-00000_p01.jpg"], "page_count": 1, "split": "public_test"}
```

- `id`: mã định danh duy nhất của tài liệu, đồng thời là tên tệp kết quả cần nộp.
- `image_paths`: danh sách đường dẫn ảnh trang **tương đối so với thư mục của tập dữ liệu**, xếp theo đúng thứ tự trang.
- `page_count`: số trang của tài liệu.
- `split`: tên tập dữ liệu.

Riêng `training_set` có thêm bốn trường:

- `label_path`: nhãn Markdown của toàn tài liệu, ví dụ `labels/train-00000.md`.
- `page_label_paths`: nhãn Markdown tách riêng theo từng trang.
- `difficulty`: mức độ khó, nhận giá trị `M1`, `M2`, `M3` hoặc `M4`.
- `attributes`: đặc điểm của tài liệu, gồm `border_mode`, `table_count`, `page_count`, `max_columns`, `max_data_rows`, `has_bold`, `has_merge`, `has_multiline`, `has_escaped_pipe`, `spans_two_pages` và `long_table_crosses_pages`.

### Quy ước nhãn Markdown

Nhãn sử dụng Markdown mở rộng với các quy ước bắt buộc sau:

- `[[H]]`: ô tiếp nối của một vùng gộp theo chiều ngang.
- `[[V]]`: ô tiếp nối của một vùng gộp theo chiều dọc.
- `<br>`: xuống dòng trong cùng một ô.
- `\|`: ký tự `|` xuất hiện trong nội dung ô.
- `**nội dung**`: nội dung in đậm.

Mỗi bảng phải có hàng phân cách Markdown gồm các ô `---`. Nếu một tài liệu có nhiều bảng, các bảng phải được phân cách bằng đúng một dòng trống.

Ví dụ một bảng ba cột có đủ các quy ước trên:

```text
| **Khu vực** | **Kế hoạch** | **Thực hiện** |
| --- | --- | --- |
| **Tổng hợp quý I** | [[H]] | [[H]] |
| Miền Bắc | 2.480 | 3.340 |
| [[V]] | 1.490 | 2.190 |
| Miền Nam | 4.680<br>(đã điều chỉnh) | 4.180 |
```

Hàng thứ ba là một tiêu đề gộp ngang cả ba cột. Ô `[[V]]` ở hàng thứ năm cho biết ô `Miền Bắc` phía trên kéo dài xuống hàng này. Ô cuối cùng của hàng thứ sáu chứa hai dòng văn bản trong cùng một ô.

## 3. Cấu trúc file nộp

Các đội thi cần nộp **01 file ZIP**. Trong ZIP, mỗi tài liệu của tập kiểm tra phải có đúng một tệp `{id}.md`:

```text
submission.zip
|-- public_test-00000.md
|-- public_test-00001.md
|-- ...
```

Đối với giai đoạn private test, tên tệp sử dụng `id` trong `private_test/manifest.jsonl`.

Trình chấm gom mọi tệp `{id}.md` ở bất kỳ vị trí nào trong ZIP và bỏ qua các tệp khác, nên nộp kèm notebook hay mã nguồn cũng không sao. Điều bắt buộc là **tên tệp phải đúng `{id}.md`**.

Mỗi tệp Markdown chỉ được chứa các bảng kết quả, không chứa code fence hoặc văn bản bên ngoài bảng. Tài liệu bị thiếu tệp, tệp rỗng, bảng sai cú pháp hoặc cấu trúc ô gộp không hợp lệ sẽ nhận 0 điểm cho tài liệu đó.

## 4. Thang đo đánh giá

Điểm của mỗi tài liệu được tính theo công thức:

```math
Document_Score=0,90×TEDS+0,10×Bold-F1
```

Trong đó:

- `TEDS` đánh giá mức độ tương đồng giữa cấu trúc và nội dung của bảng dự đoán với nhãn chuẩn.
- `Bold-F1` đánh giá độ chính xác của các nội dung được đánh dấu in đậm.

Điểm của bài nộp là trung bình điểm của toàn bộ tài liệu, quy đổi về thang 100:

```math
Score=100×1N∑i=1NDocument_Scorei
```

Điểm hiển thị trên bảng xếp hạng được chuẩn hoá từ `Score` theo công thức:

```math
Final_Score={100×Score−MinMax−Min,neˆˊu Score>Min0,neˆˊu Score≤Min
```

Trong đó:

- `Min`: ngưỡng tối thiểu do Ban tổ chức quy định cho tác vụ.
- `Max`: điểm cao nhất hiện có trên bảng xếp hạng của tác vụ.

Mỗi khi `Max` thay đổi, điểm chuẩn hoá của toàn bộ đội thi được tính lại theo công thức trên.

Tệp thiếu, rỗng hoặc không đúng cú pháp nhận điểm 0 cho tài liệu tương ứng. Kết quả trên `public_test` được dùng để phản hồi trong thời gian thi; thứ hạng cuối cùng được xác định bằng `private_test`.

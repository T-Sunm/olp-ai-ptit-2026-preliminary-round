# Tutorial: Xây dựng hệ thống trích xuất bảng từ ảnh tài liệu (Olympic AI)

## 1. Giới thiệu

Trong nhiều hoạt động hằng ngày, con người phải đọc bảng trong báo cáo, hóa đơn, hồ sơ, hợp đồng và biểu mẫu hành chính để lấy ra thông tin cần thiết. Khi xử lý thủ công, người đọc phải xác định từng hàng, từng cột, nhận biết các ô được gộp rồi nhập hoặc chuyển thông tin sang hệ thống khác. Công việc này mất nhiều thời gian khi số lượng tài liệu tăng lên và dễ xảy ra sai sót nếu bảng có cấu trúc phức tạp hoặc kéo dài qua nhiều trang. Vì bản quét chỉ tồn tại dưới dạng các điểm ảnh, phần mềm chưa thể trực tiếp tìm kiếm, tổng hợp hoặc phân tích dữ liệu bên trong bảng.

**[CHÈN HÌNH 1: `assets/doc2table/intro.png`]**

*Hình 1. Từ ảnh tài liệu đến dữ liệu bảng có cấu trúc phục vụ tìm kiếm, phân tích và tự động hóa.*

Từ nhu cầu đó hình thành bài toán **Document Image Table Extraction**, tức trích xuất bảng từ ảnh tài liệu. Hệ thống nhận vào một hoặc nhiều ảnh trang và cần khôi phục bảng dưới dạng dữ liệu có cấu trúc. Công nghệ nhận dạng ký tự quang học (**Optical Character Recognition**, viết tắt là **OCR**) giúp đọc từ và con số trong ảnh. Quá trình trích xuất bảng còn phải xác định vị trí bảng, các hàng, các cột, ô gộp và gán nội dung vào đúng ô. Kết quả cần giữ được cả nội dung và cấu trúc của bảng.

Trong Olympic AI PTIT 2026, bài toán này được đặt trong bối cảnh trích xuất bảng từ ảnh tài liệu. Các yêu cầu về cấu trúc đầu ra và cách chấm điểm được trình bày ở phần tiếp theo.

## 2. Phân tích đề thi

### 2.1. Thể lệ và yêu cầu của cuộc thi

Trong bài thi, đơn vị xử lý là một tài liệu. Mỗi tài liệu gồm một hoặc hai ảnh trang A4 và có thể chứa một hoặc nhiều bảng. Hệ thống cần phát hiện đầy đủ các bảng, giữ đúng thứ tự xuất hiện và khôi phục nội dung, số hàng, số cột, các ô gộp, nội dung nhiều dòng và định dạng in đậm.

Các yêu cầu này có thể chia thành hai phần:

- **Content Recognition**, tức nhận dạng nội dung, xác định văn bản xuất hiện trong bảng.
- **Structure Reconstruction**, tức khôi phục cấu trúc, xác định cách nội dung được tổ chức theo hàng, cột và các ô.

**[CHÈN HÌNH 2.1: Input Document → Content Recognition + Structure Reconstruction → Extended Markdown]** ([table_extraction_task_overview.pdf](../../assets/doc2table/table_extraction_task_overview.pdf))

*Hình 2.1. Hai thành phần chính trong quá trình khôi phục bảng từ ảnh tài liệu.*

Kết quả được lưu dưới dạng **Extended Markdown**, tức Markdown mở rộng. Bên cạnh cú pháp bảng Markdown thông thường, bài thi sử dụng thêm một số quy ước:

- `[[H]]` đánh dấu phần tiếp tục của một ô được gộp theo chiều ngang.
- `[[V]]` đánh dấu phần tiếp tục của một ô được gộp theo chiều dọc.
- `<br>` biểu diễn xuống dòng bên trong một ô.
- `\|` biểu diễn ký tự `|` xuất hiện trong nội dung.
- `**text**` biểu diễn nội dung in đậm.

**[CHÈN HÌNH 2.2: Document Score gồm TEDS và Bold-F1]** ([document_score_metrics.pdf](../../assets/doc2table/document_score_metrics.pdf))

*Hình 2.2. Cách TEDS và Bold-F1 đóng góp vào điểm của mỗi tài liệu.*

TEDS giữ vai trò chính trong Document Score, nên các lỗi về hàng, cột, vị trí nội dung và quan hệ ô gộp ảnh hưởng đáng kể đến kết quả. Điều này khiến độ chính xác của cấu trúc bảng trở thành một phần quan trọng của lời giải bên cạnh chất lượng nhận dạng văn bản.

Kết quả đầu ra còn phải đáp ứng các điều kiện hợp lệ của bài thi. Một tài liệu sẽ nhận 0 điểm nếu thiếu file kết quả, file rỗng, bảng sai cú pháp hoặc cấu trúc ô gộp không hợp lệ.

# Tutorial: Xây dựng hệ thống trích xuất bảng từ ảnh tài liệu (Olympic AI)

## 1. Giới thiệu

Phần mở đầu giới thiệu bài toán trích xuất bảng từ ảnh tài liệu và kết quả cần tạo ra. Một document có thể chứa một hoặc nhiều bảng trên một hoặc hai trang. Hệ thống phải khôi phục nội dung, cấu trúc và định dạng của bảng dưới dạng Extended Markdown để phần mềm có thể tiếp tục tìm kiếm, tổng hợp hoặc phân tích.

**[CHÈN HÌNH 1: `assets/doc2table/intro.png`]**

*Hình 1. Từ câu hỏi của người dùng và ảnh tài liệu đến dữ liệu bảng có cấu trúc phục vụ phân tích.*

## 2. Phân tích đề thi

### 2.1. Thể lệ và yêu cầu của cuộc thi

Phần này làm rõ:

- Định dạng input và output.
- Quan hệ giữa document, page và table.
- Những thông tin cần khôi phục: nội dung, hàng, cột, merged cells, multiline và bold.
- Quy ước `[[H]]`, `[[V]]`, `<br>`, `\|` và `**text**`.
- TEDS, Bold-F1 và cách tính Document Score.
- Những điều kiện khiến một file kết quả không hợp lệ.

**[CHÈN HÌNH 2.1: Input Document → Content Recognition + Structure Reconstruction → Extended Markdown (sinh từ cell visualization)]**

*Hình 2.1. Nội dung và cấu trúc của bảng được phục hồi để tạo kết quả Extended Markdown.*

**[CHÈN HÌNH 2.2: Document Score gồm 90% TEDS và 10% Bold-F1 (sinh từ cell EDA)]**

*Hình 2.2. Hai thành phần của Document Score và những loại lỗi ảnh hưởng đến từng metric.*

### 2.2. Dữ liệu

Phần phân tích dữ liệu tập trung vào những đặc điểm ảnh hưởng trực tiếp đến cách thiết kế lời giải. Public test và private test chỉ chứa M1 và M2, vì vậy tutorial ưu tiên hai nhóm này.

#### 2.2.1. Tổng quan dữ liệu và difficulty

- Cấu trúc dữ liệu và `manifest.jsonl`.
- Số document, page và table theo difficulty.
- Tỷ lệ xuất hiện của merge, multiline, escaped pipe và cross-page table.

**[CHÈN HÌNH 2.3: Dataset scale | Structural attribute heatmap (sinh từ cell EDA)]**

*Hình 2.3. Quy mô dữ liệu và tỷ lệ xuất hiện của các đặc điểm cấu trúc trong bốn mức độ M1 đến M4.*

#### 2.2.2. Page layout và grid geometry

- M1 chỉ có trường hợp một bảng trên một trang.
- M2 có các layout `1T1P`, `2T1P` và `1T2P`.
- Số hàng và số cột thay đổi giữa các bảng, kể cả trong cùng một difficulty.

**[CHÈN HÌNH 2.4: Các sample `1T1P`, `2T1P` và `1T2P` (sinh từ cell EDA)]**

*Hình 2.4. Ba dạng page và table layout xuất hiện trong M1 và M2.*

#### 2.2.3. Merge và content characteristics

- M1 không có merged cells hoặc multiline content.
- M2 có horizontal merge, vertical merge và multiline content.
- Atomic grid và logical table là hai tầng biểu diễn khác nhau.

**[CHÈN HÌNH 2.5: Grid-size distribution | Merge prevalence | Multiline sample (sinh từ cell EDA)]**

*Hình 2.5. Kích thước grid, merged cells và multiline content trong M1 và M2.*

#### 2.2.4. Các grammar của M2

- Ba hàng đầu tạo thành một header có cấu trúc ổn định.
- Bold formatting phụ thuộc vào vai trò của hàng và page context.
- Trang thứ hai của cross-page table lặp lại ba hàng header.

**[CHÈN HÌNH 2.6: Header grammar | Bold grammar | Cross-page continuation (sinh từ cell EDA)]**

*Hình 2.6. Các pattern về header, bold và cross-page continuation được quan sát trong M2 training data.*

### 2.3. Hướng triển khai

Các quan sát từ dữ liệu dẫn đến bảy bài toán trong baseline:

1. Phát hiện vùng bảng.
2. Phục hồi atomic grid.
3. Gom atomic cells thành logical cells.
4. Nhận dạng nội dung trong từng logical cell.
5. Khôi phục bold formatting.
6. Xử lý nhiều bảng và bảng kéo dài qua hai trang.
7. Sinh Extended Markdown hợp lệ.

Baseline dùng OpenCV để phục hồi cấu trúc, VietOCR để nhận dạng nội dung và các rule rút ra từ M1/M2 để xử lý merge, bold và cross-page continuation.

### 2.4. Kiến thức cần có

Đối với challenge này, người tham gia cần có nền tảng về xử lý tài liệu, thị giác máy tính và dữ liệu có cấu trúc. Những kiến thức này hỗ trợ quá trình phân tích đề, đọc dữ liệu và hiểu các thành phần của lời giải.

Về mặt lý thuyết, một số nhóm kiến thức đáng chú ý gồm:

- Optical Character Recognition và xử lý tài liệu: hiểu cách văn bản được nhận diện từ ảnh, cách vị trí nội dung được biểu diễn và cách bố cục tài liệu ảnh hưởng đến kết quả.
- Computer Vision cơ bản: nắm các thao tác xử lý ảnh, phát hiện vùng quan tâm và biểu diễn các đối tượng hình học trong ảnh.
- Học máy và học sâu cơ bản: hiểu quy trình sử dụng mô hình đã huấn luyện để suy luận trên dữ liệu mới và vai trò của các mô hình nhận dạng ảnh.
- Xử lý dữ liệu có cấu trúc: hiểu cách biểu diễn bảng theo hàng, cột, ô và các quan hệ giữa những ô trong bảng.
- Đánh giá mô hình: hiểu cách metric phản ánh chất lượng nhận dạng nội dung, cấu trúc và định dạng của kết quả.

Về mặt thực hành, người tham gia nên sử dụng được Python và làm quen với các thư viện như NumPy, OpenCV, PIL/Pillow và PyTorch. Pandas và Matplotlib cũng hữu ích khi khám phá dữ liệu và trực quan hóa kết quả.

## 3. Xây dựng lời giải

### 3.1. Kiến trúc tổng thể

Pipeline phục hồi cấu trúc bảng trước, nhận dạng nội dung sau, rồi kết hợp kết quả ở cấp document để sinh Extended Markdown.

**[CHÈN HÌNH 3.1: `assets/doc2table.png`]**

*Hình 3.1. Kiến trúc tổng thể của hệ thống Doc2Table.*

Ba cấu trúc dữ liệu được truyền qua các bước của pipeline:

- `GridTable` lưu bounding box, các grid edges và logical regions.
- `CellRegion` lưu phạm vi của một logical cell trên atomic grid.
- `TableResult` kết hợp geometry, nội dung OCR và stroke scores.

### 3.2. Tiền xử lý ảnh

Ảnh xám được tăng tương phản bằng CLAHE. Otsu thresholding sau đó tạo binary image với quy ước nền bằng `0`, còn chữ và đường kẻ bằng `255`.

Luồng xử lý:

```text
Grayscale → CLAHE → Otsu thresholding → Binary inversion
```

**[CHÈN HÌNH 3.2: Grayscale → CLAHE → Otsu → Binary Image (sinh từ cell visualization)]**

*Hình 3.2. Ảnh xám được tăng tương phản và nhị phân hóa để làm rõ chữ cùng các đường kẻ của bảng.*

Notebook có sẵn hàm `deskew_gray()`, nhưng vòng inference hiện tại giả định các trang đã được căn thẳng nên không gọi bước này.

### 3.3. Phát hiện vùng bảng

Directional morphology tách các đường ngang và dọc khỏi binary image. Hai line masks được ghép thành grid mask, sau đó external contours xác định bounding box của từng bảng.

Luồng xử lý:

```text
Binary image
→ Horizontal and vertical line masks
→ Joined grid mask
→ External contours
→ Table bounding boxes
```

Các table candidates được lọc theo chiều rộng, chiều cao, diện tích và số lượng grid edges. Khi một trang chứa nhiều bảng, kết quả được sắp xếp theo vị trí từ trên xuống dưới và từ trái sang phải.

**[CHÈN HÌNH 3.3: Binary Image → Line Masks → Grid Mask → Table Bounding Boxes (sinh từ cell visualization)]**

*Hình 3.3. Directional morphology và contour detection chuyển binary image thành các vùng bảng trên trang.*

### 3.4. Phục hồi atomic grid

Projection trên vertical mask tạo candidate column boundaries. Horizontal mask được xử lý tương tự để tìm row boundaries. Các response gần nhau được gom thành line runs và deduplicate trước khi tạo `x_edges` và `y_edges`.

Luồng xử lý:

```text
Line masks
→ Axis projections
→ Line runs
→ Edge deduplication
→ x_edges, y_edges
→ Atomic grid
```

Table bounding box bổ sung outer edge khi projection không tìm được boundary đủ gần mép bảng. Mỗi cặp edge liên tiếp tạo một atomic cell:

$$
A_{r,c}=[x_c,x_{c+1})\times[y_r,y_{r+1})
$$

**[CHÈN HÌNH 3.4: Line Masks → Axis Projections → Grid Edges → Atomic Grid (sinh từ cell visualization)]**

*Hình 3.4. Projection trên hai line masks tạo các row và column boundaries của atomic grid.*

### 3.5. Phục hồi logical cells

Atomic grid mới chỉ là phép chia hình học. Một logical cell có thể phủ nhiều atomic positions do horizontal hoặc vertical merge.

Baseline nhận diện M2 từ số cột và chiều cao các hàng đầu. Với bảng M2, horizontal merge trong header được phục hồi từ three-row header grammar. Vertical merge được suy ra từ local separator coverage trong từng cột:

$$
\text{coverage}
=
\frac{\text{số vị trí có line evidence}}
{\text{chiều rộng usable}}
$$

Hai atomic cells được nối khi:

$$
\text{coverage}<0.20
$$

Union-Find gom các merge relations thành connected components. Component tạo thành hình chữ nhật đầy đủ sẽ trở thành một `CellRegion`; các component còn lại được giữ dưới dạng những atomic cells riêng.

Vị trí trên trái của `CellRegion` là anchor chứa nội dung. Các vị trí còn lại dùng `[[H]]` hoặc `[[V]]` để biểu diễn phần tiếp tục của merged cell.

**[CHÈN HÌNH 3.5: Atomic Grid → Separator Evidence → Merge Relations → CellRegion và Merge Markers (sinh từ cell visualization)]**

*Hình 3.5. Separator evidence và M2 header grammar được dùng để tạo logical cells, anchor và merge markers.*

### 3.6. Nhận dạng nội dung ô

Mỗi `CellRegion` xác định vùng pixel đầy đủ của một logical cell. Pipeline thu crop vào một khoảng nhỏ để giảm ảnh hưởng của table borders, sau đó tách các text bands theo chiều dọc và đưa từng band qua VietOCR.

Luồng xử lý:

```text
Logical cell
→ Crop and remove border margin
→ Split text bands
→ VietOCR
→ Join with <br>
→ Store at anchor
```

Kết quả của các text bands được nối bằng `<br>`. Ký tự `|` trong nội dung được chuyển thành `\|`. Text chỉ được ghi tại anchor; các merge markers trong cell matrix được giữ nguyên.

**[CHÈN HÌNH 3.6: Logical Cell → Text Bands → VietOCR → Cell Content (sinh từ cell visualization)]**

*Hình 3.6. Logical cell được crop, tách thành các text bands và nhận dạng trước khi nội dung được ghi vào anchor.*

### 3.7. Khôi phục định dạng

Bold được phục hồi từ vai trò của hàng và stroke evidence:

- Với M1, hàng đầu và hàng cuối được bold.
- Với M2, ba hàng header được bold.
- Với terminal row của M2, baseline dùng median stroke score làm tín hiệu quyết định.

$$
\operatorname{median}(\text{stroke scores})\ge 0.08
$$

Rule chỉ áp dụng cho các anchor có nội dung. Merge markers và ô rỗng được giữ nguyên.

**[CHÈN HÌNH 3.7: Cell Roles + Stroke Scores → Bold Formatting (sinh từ cell visualization)]**

*Hình 3.7. Baseline khôi phục bold từ vai trò của hàng và stroke evidence tại terminal row của M2.*

### 3.8. Xử lý ở cấp document

Một trang có thể chứa nhiều table regions. Pipeline xử lý từng region độc lập rồi giữ kết quả theo thứ tự xuất hiện trên trang.

Với document hai trang, cross-page stitching chỉ được thử khi mỗi trang có đúng một bảng. Hai bảng phải có cùng số cột và normalized `x_edges` tương thích:

$$
\max_i
\left|
\tilde{x}^{(1)}_i-
\tilde{x}^{(2)}_i
\right|
\le 0.025
$$

Khi điều kiện được thỏa mãn, ba hàng header lặp lại của trang thứ hai được bỏ trước khi nối cell matrices:

```python
page1.cells + page2.cells[3:]
```

**[CHÈN HÌNH 3.8: Multiple Tables | Cross-Page Stitching (sinh từ cell visualization)]**

*Hình 3.8. Pipeline giữ thứ tự của nhiều bảng trên một trang và nối hai page tables sau khi loại header lặp lại.*

### 3.9. Sinh Extended Markdown

Cell matrix cuối cùng đã chứa text, `[[H]]`, `[[V]]`, `<br>`, escaped pipes và bold markers. Serializer nối các cell bằng `" | "`, thêm pipe ở hai đầu hàng và chèn separator row sau hàng đầu tiên.

Nhiều bảng trong cùng document được ngăn cách bằng một dòng trống. Trước khi ghi file, kết quả được kiểm tra số cột, separator row và cú pháp Markdown. Mỗi document tạo một file `.md`.

**[CHÈN HÌNH 3.9: Final Cell Matrix → Extended Markdown (sinh từ cell visualization)]**

*Hình 3.9. Cell matrix được serialize thành Extended Markdown trong khi vẫn giữ merge, multiline và bold formatting.*

## 4. Kết quả đánh giá

Phần này sẽ được hoàn thiện sau khi chạy thực nghiệm.

### 4.1. Thiết lập đánh giá

- Phạm vi training set: `[M1/M2 hoặc toàn bộ, điền sau]`
- Nguồn kết quả private test: `[điền sau]`
- Số lượng document: `[điền sau]`
- Thiết bị: `[điền sau]`
- Thời gian xử lý: `[điền sau]`

### 4.2. Kết quả định lượng

| Metric | Training set | Private test |
| --- | ---: | ---: |
| TEDS | `[điền sau]` | `[điền nếu hệ thống trả về]` |
| Bold-F1 | `[điền sau]` | `[điền nếu hệ thống trả về]` |
| Document Score | `[điền sau]` | `[điền sau]` |
| Tỷ lệ trang phát hiện được lưới | `[điền sau]` | `[điền sau]` |
| Thời gian trung bình mỗi document | `[điền sau]` | `[điền sau]` |

**[CHÈN HÌNH 4.1: Kết quả trên Training Set | Kết quả trên Private Test (ghép trong một hình)]**

*Hình 4.1. Kết quả đánh giá của baseline trên training set và private test.*

### 4.3. Nhận xét kết quả

- So sánh kết quả giữa training set và private test.
- Nhận xét về chất lượng phục hồi cấu trúc và nội dung OCR.
- Ghi nhận các lỗi merge, multiline hoặc bold xuất hiện trong quá trình kiểm tra.

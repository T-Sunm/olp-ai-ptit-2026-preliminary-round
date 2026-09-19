# Presentation Outline — Document Image Table Extraction

**Thời lượng:** 180 phút, gồm 10 phút nghỉ và 10 phút Q&A  
**Đối tượng:** Người mới học Computer Vision, đã biết Python cơ bản  
**Mục tiêu:** Hiểu pipeline Doc2Table và cơ chế của các thuật toán biến ảnh tài liệu thành bảng Markdown có cấu trúc.

> Đây là technical deep dive theo một case study xuyên suốt. Mỗi thuật toán được giảng tại đúng nơi nó xuất hiện trong pipeline.

## Kết quả mong đợi

Sau buổi học, người nghe có thể:

- phân biệt OCR, table detection và structure reconstruction;
- giải thích cách Canny–Hough hỗ trợ deskew;
- giải thích vai trò của CLAHE, Otsu và morphology;
- hiểu cách contour, projection và segment coverage phục hồi grid;
- phân biệt atomic cell, logical cell và CellRegion;
- mô tả cách OCR, merge markers và formatting tạo Extended Markdown;
- nhận diện các giả định và giới hạn của baseline M1/M2.

## Phân bổ thời gian

| Phần | Thời lượng |
| --- | ---: |
| 1. Problem & Data | 12 phút |
| 2. Solution Architecture | 6 phút |
| 3. Document Deskew: Sobel, Canny & Hough | 25 phút |
| 4. Image Enhancement & Otsu Binarization | 20 phút |
| 5. Morphology & Directional Line Extraction | 20 phút |
| Break | 10 phút |
| 6. Contour-Based Table Localization | 12 phút |
| 7. Projection-Based Grid Recovery | 18 phút |
| 8. Merged-Cell & Logical-Region Reconstruction | 25 phút |
| 9. OCR, Cross-Page & Formatting Recovery | 15 phút |
| 10. Results, Limitations & Takeaways | 7 phút |
| Q&A | 10 phút |
| **Tổng** | **180 phút** |

---

# 1. Problem & Data

**Thời lượng:** 12 phút — khoảng 5 slides.

## From Pixels to Structured Tables

Input là ảnh tài liệu. Output không chỉ chứa text mà phải giữ hàng–cột, merged cells, multiline content, bold formatting và thứ tự bảng giữa các trang.

**[HÌNH 1: Document image → Extended Markdown]**

## OCR Is Not Table Reconstruction

OCR trả lời: “Trong vùng ảnh này có chữ gì?”

Reconstruction trả lời: “Nội dung nằm ở hàng nào, cột nào và span bao nhiêu ô?”

> **OCR đọc nội dung; reconstruction phục hồi quan hệ giữa các nội dung.**

## Atomic Cells and Logical Cells

- **Grid edges:** ranh giới theo trục x và y.
- **Atomic cell:** vùng nhỏ nhất giữa hai cặp edges liên tiếp.
- **Logical cell:** một hoặc nhiều atomic cells sau khi xét merge.
- **Anchor:** vị trí trên-trái giữ nội dung của logical cell.

**[HÌNH 2: Atomic grid → merged areas → logical cells]**

## Dataset Observations

Baseline tập trung vào M1/M2:

| Observation | Design decision |
| --- | --- |
| Bordered grid tương đối rõ | Directional morphology |
| Grid tạo connected component | Contour localization |
| Lines tạo projection peaks | Recover x_edges và y_edges |
| Separator có thể thiếu cục bộ | Segment coverage |
| Có merged cells | Atomic-to-logical reconstruction |

---

# 2. Solution Architecture

**Thời lượng:** 6 phút — khoảng 3 slides.

## End-to-End Pipeline

Luồng tổng thể bắt đầu từ **Document Images**, đi qua **Table Detection & Structure Reconstruction**, **Cell Content Recognition**, **Cross-Page Table Consolidation** và **Formatting Recovery**, trước khi kết thúc ở **Extended Markdown Serialization**.

Riêng bên trong reconstruction, ảnh lần lượt được tăng cường, tách đường kẻ, định vị bảng rồi phục hồi grid và logical cells.

**[HÌNH 3: End-to-End Architecture Diagram]**

## Representation Flow

Trong suốt pipeline, dữ liệu ngày càng có cấu trúc hơn: từ pixels thành binary mask, line masks, table bounding boxes, grid edges, atomic grid, logical CellRegions, table matrix có nội dung và cuối cùng là Extended Markdown.

Deskew là bước robustness preprocessing trước pipeline chính. Nó đặc biệt cần thiết khi áp dụng cho ảnh scan hoặc ảnh chụp thực tế.

---

# 3. Document Deskew: Sobel, Canny & Hough

**Thời lượng:** 25 phút — khoảng 10 slides.

## Why Deskew?

Khi trang bị nghiêng:

- directional kernels không còn khớp tốt;
- projection peaks bị trải rộng;
- grid edges và cell crops kém ổn định.

**[HÌNH 4: Table ở 0°, 2° và 5°]**

## Image Gradient and Sobel

Edge xuất hiện tại nơi cường độ sáng thay đổi nhanh. Hai đạo hàm riêng mô tả mức thay đổi theo phương ngang và phương dọc:

$$
G_x = \frac{\partial I}{\partial x},
\qquad
G_y = \frac{\partial I}{\partial y}
$$

Từ đó, độ mạnh và hướng của gradient được tính bởi:

$$
G = \sqrt{G_x^2 + G_y^2},
\qquad
\theta = \operatorname{atan2}(G_y, G_x)
$$

Sobel dùng hai kernel 3 × 3:

- Gx phản ứng mạnh với vertical edges;
- Gy phản ứng mạnh với horizontal edges.

Tính tay một convolution nhỏ để minh họa cách pixel neighborhood trở thành edge response.

**[HÌNH 5: Image patch → Sobel Gx/Gy → gradient]**

## Canny Edge Detection

Canny bắt đầu bằng Gaussian smoothing để giảm noise, sau đó tính gradient, làm mảnh edge bằng non-maximum suppression, phân loại response bằng hai ngưỡng và cuối cùng nối edge bằng hysteresis.

- **Non-maximum suppression:** giữ local maximum theo hướng gradient để làm edge mỏng.
- **Double threshold:** chia response thành strong, weak và rejected.
- **Hysteresis:** chỉ giữ weak edge nếu nó nối với strong edge.

> Canny sử dụng cả độ mạnh lẫn tính liên tục của edge.

**[HÌNH 6: Gradient → NMS → strong/weak edges → final edges]**

## Hough Line Transform

Thay vì dùng dạng hệ số góc dễ gặp vấn đề với đường thẳng đứng, Hough biểu diễn đường thẳng bằng:

$$
\rho = x\cos\theta + y\sin\theta
$$

Mỗi edge pixel vote cho các line có thể đi qua nó. Các pixels thẳng hàng tạo accumulator peak tại cùng một cặp rho–theta.

**[HÌNH 7: Collinear pixels → Hough sinusoids → accumulator peak]**

Chỉ giải thích tác động của các tham số chính: rho resolution, theta resolution, vote threshold, minLineLength và maxLineGap.

## Estimating and Correcting Skew

Từ trang xám, Canny tạo edge evidence và Hough gom evidence đó thành các line segments. Sau khi chỉ giữ các đường gần ngang, hệ thống lấy median của các góc rồi xoay ảnh theo góc bù. Median được chọn vì ít nhạy với một vài line candidates sai hơn mean.

**[DEMO 1: Canny/Hough lines và ảnh trước–sau deskew]**

## Failure Modes

- decorative lines tạo dominant angle sai;
- quá ít line dài;
- góc nghiêng vượt candidate range;
- interpolation làm nét mảnh bị mờ.

### Checkpoint

> Canny trả về edge pixels; Hough bổ sung thông tin hình học nào?

---

# 4. Image Enhancement & Otsu Binarization

**Thời lượng:** 20 phút — khoảng 8 slides.

## Why Enhancement?

Scan nhạt hoặc illumination không đều khiến một threshold chung dễ làm mất nét ở vùng này nhưng giữ noise ở vùng khác.

## Histogram and Global Equalization

Histogram mô tả phân bố mức sáng. Global equalization dùng CDF để trải intensity, nhưng một mapping chung có thể không phù hợp với mọi vùng trên trang.

**[HÌNH 8: Ảnh contrast thấp và histogram]**

## CLAHE

CLAHE chia ảnh thành các tiles nhỏ, cân bằng histogram trong từng tile, cắt bớt những histogram peaks quá lớn rồi nội suy giữa các tiles để tránh tạo ranh giới giả.

- local processing xử lý illumination không đều;
- clipLimit hạn chế khuếch đại noise;
- interpolation tránh boundary artifacts.

Mục tiêu là tăng khả năng tách foreground/background, không chỉ làm ảnh đẹp hơn.

## Otsu Thresholding

Otsu thử các candidate thresholds và chọn ngưỡng:

- minimize within-class variance; hoặc
- maximize between-class variance.

Với mỗi threshold đang xét, within-class variance có thể trình bày bằng:

$$
\sigma_w^2(t)
=
\omega_0(t)\sigma_0^2(t)
+
\omega_1(t)\sigma_1^2(t)
$$

Otsu chọn:

$$
t^* = \underset{t}{\arg\min}\;\sigma_w^2(t)
$$

Dùng một histogram nhỏ để tính 2–3 candidate thresholds, không tính toàn bộ 256 mức.

**[HÌNH 9: Histogram, candidate thresholds và Otsu threshold]**

## Inverted Binary Convention

Trong implementation, Otsu được kết hợp với inverted binary threshold. Vì vậy nền giấy được đưa về giá trị 0, còn chữ và đường kẻ trở thành foreground có giá trị 255.

**[HÌNH 10: Grayscale → CLAHE → inverted Otsu binary]**

## Limitation

Otsu kém ổn định khi histogram không tách thành hai nhóm rõ hoặc illumination thay đổi quá mạnh.

### Checkpoint

> CLAHE và Otsu giải quyết hai vấn đề khác nhau như thế nào?

---

# 5. Morphology & Directional Line Extraction

**Thời lượng:** 20 phút — khoảng 9 slides.

## Structuring Element

Structuring element là pattern hình học dùng để kiểm tra hoặc biến đổi foreground. Kích thước, hình dạng và origin của kernel quyết định structure được giữ.

## Core Operations

- **Erosion — fit:** giữ vị trí nơi kernel nằm vừa trong foreground.
- **Dilation — hit:** mở rộng vị trí nơi kernel chạm foreground.
- **Opening:** erosion rồi dilation, loại structure không phù hợp.
- **Closing:** dilation rồi erosion, nối gap hoặc lấp hole nhỏ.

**[HÌNH 11: Morphology trên ma trận nhị phân nhỏ]**

## Directional Kernels

Một kernel dài theo chiều ngang tạo horizontal line mask; một kernel dài theo chiều dọc tạo vertical line mask.

Text strokes thường không đủ dài liên tục nên bị loại, trong khi table rules được giữ.

- kernel quá ngắn → chữ còn sót;
- kernel quá dài → line ngắn hoặc đứt bị mất.

**[HÌNH 12: Binary image → horizontal mask + vertical mask]**

## Joining the Grid

Hai line masks được kết hợp bằng phép OR. Một lần dilation nhẹ sau đó nối các gap nhỏ, giúp toàn bộ grid trở thành connected component thuận lợi cho contour detection.

**[DEMO 2: Thay kernel length và quan sát line masks]**

### Checkpoint

> Vì sao cùng một binary image nhưng hai kernel khác nhau lại tạo hai masks khác nhau?

---

# Break

**Thời lượng:** 10 phút.

Giữ trên màn hình:

**Original → Deskewed → CLAHE → Otsu → Horizontal/Vertical Masks → Joined Grid**

---

# 6. Contour-Based Table Localization

**Thời lượng:** 12 phút — khoảng 6 slides.

## Contour, Component and Bounding Box

- connected component là tập foreground pixels liên thông;
- contour là boundary có thứ tự của component;
- bounding box là hình chữ nhật bao contour.

## Retrieval and Approximation

Baseline gọi contour detection trên joined mask với hai lựa chọn chính:

- **RETR_EXTERNAL** lấy outer contours vì stage này tìm vùng toàn bảng;
- **CHAIN_APPROX_SIMPLE** bỏ boundary points dư trên đoạn thẳng;
- **boundingRect** chuyển contour thành table box;
- size và area thresholds loại components quá nhỏ.

**[HÌNH 13: Joined mask → contour → table bounding box]**

## Why Not Use Child Contours Directly?

Child contours dễ sai khi border bị đứt, cell bị merge, text chạm border, dilation làm các vùng dính nhau hoặc dark header tạo nested contours.

Baseline dùng outer contour để localize bảng, rồi dùng line masks để phục hồi grid.

---

# 7. Projection-Based Grid Recovery

**Thời lượng:** 18 phút — khoảng 8 slides.

## Projection Profiles

Với vertical mask, hệ thống cộng foreground pixels theo chiều dọc để thu được một score tại mỗi tọa độ ngang. Với horizontal mask, phép cộng được thực hiện theo chiều ngang để thu được score tại mỗi tọa độ dọc:

$$
P_x(x) = \sum_y V(x,y),
\qquad
P_y(y) = \sum_x H(x,y)
$$

Các peaks trong projection theo chiều ngang tạo candidate x-edges, còn projection theo chiều dọc tạo candidate y-edges.

**[HÌNH 14: Line masks đặt cạnh projection plots]**

## From Peaks to Edges

Projection scores trước hết được threshold để tìm active coordinates. Các tọa độ liên tiếp được gom thành runs; mỗi run tạo một representative edge và các edges quá gần nhau được deduplicate.

Một đường dày tạo nhiều active coordinates, vì vậy không thể coi mỗi pixel là một grid edge riêng.

## Thick-Run Handling

Dark title band có thể tạo run rất dày. Nếu chỉ lấy center, hai mép cấu trúc bị collapse; baseline coi hai mép thick run là hai boundaries.

## Global Boundary vs. Local Separator

Projection phát hiện boundary toàn cục khi đủ nhiều columns có line tại vị trí đó. Nó không chứng minh line chạy qua mọi column.

**[HÌNH 15: Global y-edge nhưng thiếu local separator tại một column]**

### Checkpoint

> Projection đã trả lời câu hỏi nào và còn thiếu thông tin cục bộ nào?

---

# 8. Merged-Cell & Logical-Region Reconstruction

**Thời lượng:** 25 phút — khoảng 11 slides.

## Atomic Grid

Nếu số vertical edges và horizontal edges lần lượt là:

$$
N_x = \lvert X_{\text{edges}}\rvert,
\qquad
N_y = \lvert Y_{\text{edges}}\rvert
$$

thì kích thước atomic grid là:

$$
\text{columns} = N_x - 1,
\qquad
\text{rows} = N_y - 1
$$

Mỗi vùng giữa hai x_edges và hai y_edges liên tiếp là một atomic cell.

**[HÌNH 16: Recovered edges → atomic grid]**

## Segment Coverage

Để kiểm tra boundary giữa hai vertically adjacent cells:

Hệ thống lấy một strip nhỏ quanh y-edge trên horizontal mask, giới hạn strip trong column đang xét, trim hai đầu rồi đo tỷ lệ foreground còn lại.

- coverage cao → separator tồn tại;
- coverage thấp → separator bị thiếu → merge.

Radius xử lý line dày hoặc lệch nhẹ. Trim loại ảnh hưởng của vertical borders ở hai đầu.

Với ngưỡng hiện tại, quyết định merge có thể viết gọn thành:

$$
\operatorname{merge}(r,c)
\quad\text{nếu}\quad
\operatorname{coverage}(r,c) < 0.20
$$

> **Projection tìm boundary toàn cục; segment coverage kiểm tra boundary cục bộ.**

**[HÌNH 17: Local segment, trim area và coverage score]**

## Horizontal Merge via M2 Grammar

Baseline chưa dùng vertical-mask coverage cho mọi horizontal merge. Với M2:

- merge toàn bộ title row;
- merge hai grouped headers;
- chưa hỗ trợ arbitrary horizontal merges trong body.

Đây là specialization cho target M1/M2.

## Union-Find

Mỗi atomic cell bắt đầu là một node riêng. Khi merge evidence nối A với B và B với C, tính bắc cầu của union-find đưa cả ba vào cùng một component.

Component phải tạo rectangular span để tránh logical cell hình chữ L.

## Building CellRegion

Một logical region được biểu diễn bởi bốn chỉ số:

$$
\operatorname{CellRegion}(r_0, r_1, c_0, c_1)
$$

Hai chỉ số kết thúc trong biểu diễn trên là exclusive:

- x_edges/y_edges giữ atomic geometry;
- GridTable.regions mô tả logical grouping.

Không rewrite edges sau merge.

**[HÌNH 18: Atomic cells → union groups → CellRegions]**

## Anchor and Merge Markers

Vị trí trên-trái của region là anchor và giữ OCR text:

- cùng hàng với anchor → [[H]];
- ở hàng thấp hơn → [[V]].

Markers được sinh sau reconstruction và không được OCR.

**[HÌNH 19: Logical region → anchor + H/V markers]**

## Short Exercise

Cho một grid nhỏ cùng coverage scores. Người nghe xác định các unions, viết CellRegion và đặt anchor/H/V markers.

---

# 9. OCR, Cross-Page & Formatting Recovery

**Thời lượng:** 15 phút — khoảng 7 slides.

## Crop Logical Cells

Pixel bounds được suy ra trực tiếp từ atomic edges:

$$
x_{\min}=X_{\text{edges}}[c_0],
\quad
x_{\max}=X_{\text{edges}}[c_1],
\quad
y_{\min}=Y_{\text{edges}}[r_0],
\quad
y_{\max}=Y_{\text{edges}}[r_1]
$$

Một logical cell tạo một crop và được OCR một lần.

## Multiline Text Bands

Mỗi cell crop được chuyển thành binary ink mask và loại border. Một vertical closing nhỏ nối dấu tiếng Việt với glyph body; row projection sau đó tìm các text bands. Các bands được OCR từ trên xuống dưới và nối bằng thẻ line break.

Vertical closing giúp nối dấu tiếng Việt với glyph body.

**[HÌNH 20: Cell crop → text bands → multiline output]**

## Cross-Page Consolidation

Chỉ stitch khi mỗi page có một table, column counts bằng nhau và normalized column-edge ratios đủ gần. Repeated headers ở trang sau được loại trước khi append body.

## Type Inference and Bold Recovery

M2 type inference từ grid geometry được dùng cho header merge grammar và bold grammar. Với M2 last row, erosion-survival score cung cấp evidence về stroke thickness.

## Serialization

Table matrix cuối chứa text, line breaks, H/V markers, bold markup và escaped pipes rồi được serialize thành Extended Markdown.

---

# 10. Results, Limitations & Takeaways

**Thời lượng:** 7 phút — khoảng 4 slides.

## End-to-End Result

Hero example được nhắc lại theo dòng chuyển đổi hoàn chỉnh: **Document → Deskewed/Enhanced Image → Binary and Line Masks → Table Box → Grid Edges → Logical Cells → OCR Matrix → Extended Markdown**.

**[HÌNH 21: End-to-end hero example]**

## Main Assumptions and Limitations

- grid lines phải đủ rõ;
- trang phải tương đối thẳng hoặc deskew thành công;
- projection phải phản ánh đúng global grid;
- missing separator thường phải thực sự biểu thị merged cell;
- M2 headers phải gần grammar đã quan sát;
- arbitrary horizontal merges và borderless tables chưa được xử lý tổng quát.

## Key Takeaways

1. Table extraction là bài toán structure trước khi là bài toán OCR.
2. Deskew bảo vệ giả định horizontal/vertical của các bước sau.
3. CLAHE/Otsu tạo foreground evidence; morphology tạo line structure.
4. Contour localize bảng, projection tìm global grid, coverage kiểm tra local separators.
5. Atomic geometry và logical grouping là hai representation khác nhau.
6. Heuristic phải luôn được trình bày cùng assumption và failure mode.

---

# Q&A

**Thời lượng:** 10 phút.

Giữ architecture diagram trên màn hình để đặt mỗi câu hỏi vào đúng stage.

---

# Delivery Notes

## Ba demo cần chuẩn bị

1. **Deskew:** Canny → Hough candidates → median angle → rotated page.
2. **Line extraction:** thay đổi horizontal/vertical kernel length.
3. **Merged-cell inference:** hiển thị segment coverage và union decision.

## Nhịp giảng thống nhất

Mỗi kỹ thuật được trình bày theo cùng một nhịp: bắt đầu từ **Problem**, xây dựng **Intuition**, giải thích **Algorithm**, quan sát **Visual Result**, nối lại với **Role in the Solution**, rồi kết thúc bằng **Failure Mode**.

## Scope Guardrails

Để giữ đúng 180 phút:

- Sobel chỉ tính tay một patch;
- Canny tập trung vào NMS và hysteresis;
- Hough chỉ minh họa một accumulator peak;
- Otsu chỉ tính vài candidate thresholds;
- morphology dùng một ví dụ ma trận chung;
- union-find chỉ giảng grouping, không đi sâu path compression;
- contour border-following implementation để trong backup slides.

Phần cần bảo vệ thời gian là **Projection + Reconstruction (43 phút)**. Nếu phần đầu bị chậm, rút bớt phép tính tay thay vì cắt phần này.

## Cách diễn đạt cần tránh

- CLAHE không chỉ làm ảnh đẹp hơn; nó tăng local separability.
- Canny không tự deskew; nó cung cấp edge evidence cho Hough.
- Contour ngoài không trực tiếp trả về grid cells.
- Projection không chứng minh separator tồn tại ở mọi column.
- Union-find không tự quyết định merge; nó chỉ nhóm merge decisions.
- CellRegion không thay thế x_edges/y_edges.
- Merge markers không được OCR; chỉ anchor giữ nội dung.

# 1. Introduction

## 1.1.  The Problem: Information Trapped in Documents

Trong thực tế, nhiều thông tin quan trọng vẫn tồn tại bên trong các tài liệu như báo cáo, bảng lương, danh sách, biểu thống kê hay các biểu mẫu hành chính. Con người có thể đọc và khai thác những tài liệu này tương đối dễ dàng vì chúng ta hiểu được nội dung cũng như cách thông tin được tổ chức trên trang.

Tuy nhiên, khi muốn sử dụng những thông tin đó trong các hệ thống phần mềm, việc chỉ lưu tài liệu dưới dạng ảnh hoặc bản scan là chưa đủ. Những tác vụ như tìm kiếm, tổng hợp, phân tích hay tự động tạo báo cáo thường cần **structured data, tức dữ liệu có cấu trúc**, trong đó thông tin đã được tổ chức theo những thành phần và quan hệ rõ ràng để phần mềm có thể tiếp tục xử lý.

[image.png](attachment\:cc698066-de40-4434-98a0-a32e0172c5bb\:image.png)

**[CHÈN HÌNH 1.1: User Question → Information Extraction → Usable Result]**

*Hình 1.1. Từ tài liệu dạng ảnh đến dữ liệu có cấu trúc phục vụ các nhu cầu khai thác thông tin.*

Hình 1.1 minh họa một tình huống như vậy. Người dùng có thể đặt ra yêu cầu "Summarize learner results by class", trong khi thông tin cần thiết vẫn đang nằm trong một tài liệu dạng ảnh. Để đáp ứng yêu cầu đó, hệ thống cần lấy thông tin ra khỏi tài liệu và chuyển nó sang dữ liệu có cấu trúc để các bước phía sau có thể tiếp tục tổng hợp, tìm kiếm, phân tích hoặc tự động hóa.

Từ nhu cầu này xuất hiện bài toán **Document Image Table Extraction, tức trích xuất bảng từ ảnh tài liệu**. Input của bài toán là một hoặc nhiều ảnh tài liệu có chứa bảng. Output cần khôi phục lại bảng ở dạng mà phần mềm có thể biểu diễn và xử lý được.

Trong challenge lần này của **Olympic AI PTIT 2026**, mỗi tài liệu gồm một hoặc hai ảnh trang A4 chứa một hoặc nhiều bảng. Kết quả được lưu dưới dạng **Extended Markdown, tức Markdown mở rộng**, một cách biểu diễn bảng bổ sung thêm các quy ước để giữ lại những thông tin mà Markdown thông thường không mô tả đầy đủ. Hệ thống cần bảo toàn thứ tự bảng, nội dung văn bản, số hàng và số cột, ô gộp, nội dung nhiều dòng và định dạng in đậm.

## 1.2. From Documents to Structured Data

Ở Hình 1.1, toàn bộ quá trình biến thông tin trong tài liệu thành dữ liệu có thể sử dụng được được gom lại dưới khái niệm **Information Extraction, tức trích xuất thông tin**. Ở mức chi tiết hơn, quá trình này không diễn ra trong một bước duy nhất mà gồm nhiều mức xử lý khác nhau.

Với bài toán trích xuất bảng, hệ thống trước hết cần xác định **table region, tức vùng chứa bảng**. Một trang tài liệu có thể còn chứa logo, tiêu đề, đoạn văn, chú thích hoặc các thành phần trình bày khác. Vì output của bài toán chỉ quan tâm đến bảng, phần nằm ngoài vùng bảng cần được loại khỏi quá trình xử lý tiếp theo.

Sau khi vùng bảng đã được xác định, hệ thống tiếp tục phục hồi **Table Structure, tức cấu trúc bảng**. Cấu trúc này mô tả cách bảng được tổ chức thành hàng, cột và các vùng ô, bao gồm cả những trường hợp một ô kéo dài qua nhiều hàng hoặc nhiều cột.

**[CHÈN HÌNH 1.2: Table Region → Table Structure → Cell Content → Extended Markdown]**

*Hình 1.2. Các mức xử lý bên trong quá trình Information Extraction để chuyển bảng trong ảnh thành dữ liệu có cấu trúc.*

Khi cấu trúc đã được phục hồi, nội dung văn bản mới được gắn vào đúng cell tương ứng. Kết quả lúc này không chỉ cho biết trong ảnh có những chữ gì, mà còn cho biết mỗi nội dung thuộc hàng nào, cột nào và có quan hệ như thế nào với các ô xung quanh.

Trong challenge này, kết quả có cấu trúc được lưu dưới dạng **Extended Markdown, tức Markdown mở rộng**. Ngoài cú pháp bảng Markdown thông thường, đề bài quy định thêm một số ký hiệu để biểu diễn các đặc điểm cấu trúc và định dạng của bảng.

Các ký hiệu được quy định gồm:

- `[[H]]` biểu diễn phần tiếp tục của một ô được gộp theo chiều ngang
- `[[V]]` biểu diễn phần tiếp tục của một ô được gộp theo chiều dọc
- `<br>` biểu diễn xuống dòng bên trong một ô
- `\|` biểu diễn ký tự `|` xuất hiện trong nội dung ô
- `*text**` biểu diễn nội dung in đậm

## 1.3. The Table Extraction Task

### 1.3.1. Task Definition

Trong challenge này, mỗi **document** gồm một hoặc hai ảnh trang A4 và có thể chứa một hoặc nhiều bảng. Nhiệm vụ của hệ thống là trích xuất toàn bộ các bảng xuất hiện trong document và chuyển chúng sang định dạng **Extended Markdown** theo đúng thứ tự.

Kết quả không chỉ cần đúng phần văn bản. Hệ thống còn phải bảo toàn những thông tin quan trọng của bảng như số hàng, số cột, các ô được gộp theo chiều ngang hoặc chiều dọc, nội dung nhiều dòng trong một ô, ký tự `|` xuất hiện trong nội dung và các đoạn chữ được in đậm. Các đặc điểm này được biểu diễn trong Extended Markdown thông qua những quy ước như `[[H]]`, `[[V]]`, `<br>`, `\|` và `**nội dung**`.

Có thể xem nhiệm vụ này gồm hai thành phần chính:

- **Content Recognition, tức nhận dạng nội dung**, xác định trong từng vùng của bảng có những ký tự và văn bản gì
- **Structure Reconstruction, tức phục hồi cấu trúc**, xác định nội dung đó thuộc hàng nào, cột nào và một cell có kéo dài qua nhiều hàng hoặc nhiều cột hay không

Hai thành phần này bổ sung cho nhau. Nếu hệ thống đọc đúng nội dung nhưng đặt text vào sai cell thì cấu trúc bảng vẫn sai. Ngược lại, nếu hàng, cột và ô gộp được phục hồi đúng nhưng nội dung nhận dạng sai thì kết quả cuối cùng cũng chưa chính xác.

**[CHÈN HÌNH 1.3: Input Document → Content Recognition + Structure Reconstruction → Extended Markdown]**

*Hình 1.3. Nhiệm vụ trích xuất bảng từ ảnh tài liệu sang Extended Markdown.*

Vì vậy, **Table Extraction** trong challenge này không chỉ là bài toán đọc chữ từ ảnh. Hệ thống cần đồng thời phục hồi cả **nội dung** và **cách nội dung được tổ chức bên trong bảng**.

### 1.3.2. Evaluation Metrics

Sau khi xác định output cần tạo ra, challenge đánh giá kết quả của mỗi document bằng hai metric là **TEDS** và **Bold-F1**. Điểm của một document được tính theo công thức:

DocumentScore=0.90×TEDS+0.10×Bold−F1Document_Score = 0.90 × TEDS + 0.10 × Bold-F1

**TEDS** đánh giá mức độ tương đồng về **cấu trúc và nội dung** giữa bảng dự đoán và bảng chuẩn. Nếu hệ thống phục hồi đúng cách bảng được tổ chức, đặt nội dung vào đúng cell và giữ đúng các quan hệ ô gộp, TEDS sẽ cao. Ngược lại, những lỗi như thiếu hàng, thừa cột, đặt text sai cell hoặc phục hồi sai merged cell đều làm bảng dự đoán khác với ground truth và làm giảm TEDS.

**Bold-F1** tập trung riêng vào các nội dung được đánh dấu in đậm. Nếu những phần cần bold được phục hồi đúng và không đánh dấu nhầm các nội dung khác, Bold-F1 sẽ cao. Nếu bỏ sót nội dung in đậm hoặc đánh dấu bold sai vị trí, metric này sẽ giảm.

**[CHÈN HÌNH 1.4: Document Score gồm 90% TEDS và 10% Bold-F1, kèm minh họa prediction đúng và prediction sai]**

*Hình 1.4. Cách cấu trúc, nội dung và định dạng ảnh hưởng đến Document Score.*

Việc **TEDS chiếm 90% Document Score** cho thấy phần lớn điểm số gắn với khả năng phục hồi đúng cả cấu trúc và nội dung của bảng. Một hệ thống có thể đọc đúng phần lớn văn bản nhưng vẫn mất nhiều điểm nếu các giá trị bị đặt sai hàng, sai cột hoặc các quan hệ merge được khôi phục không chính xác.

Bên cạnh chất lượng dự đoán, challenge còn kiểm tra tính hợp lệ của output trước khi chấm điểm. Nếu document bị thiếu file kết quả, file rỗng, bảng sai cú pháp hoặc cấu trúc ô gộp không hợp lệ thì document đó sẽ nhận **0 điểm**. Đây là điều kiện hợp lệ của submission, không phải một phần trong cách TEDS được tính.

Điểm của toàn bộ bài nộp được lấy từ trung bình điểm của các document rồi quy đổi về thang 100. Điểm hiển thị trên bảng xếp hạng sau đó còn được chuẩn hóa dựa trên ngưỡng tối thiểu của task và điểm cao nhất hiện có. Kết quả trên public test được sử dụng để phản hồi trong thời gian thi, còn thứ hạng cuối cùng được xác định bằng private test.

# 2. Data Exploration

## 2.1. Dataset Overview

Training set gồm **1.100 documents**, được chia thành bốn mức độ khó từ M1 đến M4. Do một document có thể gồm nhiều trang và chứa nhiều bảng, số lượng pages và tables không tăng theo đúng số documents. Cụ thể, toàn bộ training set có **1.375 pages** và **1.616 tables**.

Phân bố theo difficulty cho thấy M1 và M2 chiếm phần lớn training set. M1 gồm 325 documents và hoàn toàn là single-page, single-table cases. M2 gồm 330 documents nhưng đã tăng lên 366 pages và 458 tables, cho thấy từ mức này bắt đầu xuất hiện các trường hợp nhiều bảng hoặc nhiều trang. M3 và M4 tiếp tục mở rộng độ phức tạp với số pages và tables trên mỗi document lớn hơn.

**[CHÈN HÌNH 2.1: Bar chart “Documents theo difficulty” và “Pages theo difficulty” từ notebook EDA]**

*Hình 2.1. Phân bố số document và số page theo từng mức độ khó trong training set.*

Một điểm quan trọng đối với solution là **public test và private test chỉ chứa M1 và M2**. Vì vậy, các mức M3 và M4 vẫn hữu ích để quan sát cách độ khó có thể tăng lên trong bài toán tổng quát, nhưng các quyết định thiết kế chính của solution sẽ tập trung vào những pattern thực sự xuất hiện trong M1 và M2.

Từ đây, câu hỏi tiếp theo không còn là "dataset có bao nhiêu mẫu", mà là:

**"Điều gì thực sự thay đổi khi difficulty tăng từ M1 lên M2, M3 và M4?"**

## 2.2. Difficulty Levels

Bốn mức **M1 → M4** không chỉ khác nhau ở kích thước bảng. Khi difficulty tăng, dataset bổ sung dần các dạng **structural complexity**, tức độ phức tạp về cấu trúc, như merged cells, multiline content, escaped pipe, nhiều bảng trong một document và table kéo dài qua nhiều trang.

Ở **M1**, bài toán có cấu trúc đơn giản nhất: mỗi document chứa đúng một bảng full-grid trên một trang, có tối đa 7 cột và không có merged cells hoặc multiline content. Sang **M2**, bảng vẫn giữ full-grid nhưng có thể lớn hơn, đồng thời xuất hiện merged cells, multiline content, nhiều bảng trên cùng một trang và một số bảng kéo dài qua hai trang.

Từ **M3**, border mode không còn đồng nhất là full-grid mà bắt đầu xuất hiện các bảng chỉ có đường ngang, zebra hoặc không có border. Đến **M4**, full-grid biến mất hoàn toàn, trong khi số cột, số trang và độ phức tạp của bố cục tiếp tục tăng.

Điều này thể hiện rõ trong EDA. Trong năm structural attributes được theo dõi ở heatmap, M1 đều có tỷ lệ 0%. Ngược lại, **100% M2 documents có ít nhất một merged cell và một multiline cell**. M2 chưa có escaped pipe. Ngoài ra, 36/330 documents, tương đương **10,9%**, gồm hai trang và toàn bộ các trường hợp này cũng là long-table continuation.

Ở M3 và M4, mỗi document đều chứa merge, multiline và escaped pipe. Tỷ lệ document hai trang tăng lần lượt lên **49,3%** và **61,2%**, trong khi tỷ lệ có long table thực sự đi qua hai trang là **30,4%** và **38,2%**.

**[CHÈN HÌNH 2.2: Heatmap “Tỷ lệ document có từng structural attribute” từ notebook EDA]**

*Hình 2.2. Tỷ lệ document có ít nhất một lần xuất hiện từng structural attribute theo difficulty.*

Cần lưu ý rằng các tỷ lệ trên được tính ở cấp **document**. Ví dụ, `has_multiline = 100%` nghĩa là mọi document trong nhóm có ít nhất một multiline cell, không có nghĩa mọi cell đều multiline. Mức độ phổ biến ở cấp cell sẽ được phân tích riêng trong phần sau.

Điểm đáng chú ý là **M2 chưa thay đổi hoàn toàn bản chất hình học của bảng so với M1**. Cả hai vẫn dựa trên full-grid. Độ khó trong phạm vi target test chủ yếu tăng do hệ thống phải phục hồi thêm các quan hệ giữa cell, nội dung nhiều dòng, nhiều bảng trong document và cross-page continuation, thay vì phải chuyển sang xử lý một loại bảng hoàn toàn khác.

Phần tiếp theo sẽ đi sâu vào các pattern bên trong M1 và M2, bao gồm page layout, table dimensions, merge topology, multiline, bold và cross-page continuation.

## 2.3. Structural & Formatting Patterns

Sau khi xác định M1 và M2 là phạm vi chính của target test, phần này đi sâu vào những pattern xuất hiện bên trong hai mức này. Thay vì chỉ nhìn dataset ở cấp difficulty, ta chuyển sang các đặc điểm trực tiếp ảnh hưởng đến cách reconstruct table, bao gồm page layout, table dimensions, merge topology, multiline content, bold formatting và cross-page continuation.

## 2.3.1. Page & Table Layout

Trước hết cần xem một document có thể chứa **bao nhiêu bảng và bao nhiêu trang**. Thông tin này quyết định liệu pipeline có thể giả định mỗi page chỉ chứa một table region và mỗi table region tương ứng với một logical table hoàn chỉnh hay không.

Trong M1, layout hoàn toàn cố định: **325/325 documents thuộc dạng `1T1P`**, tức một table trên một page. Đây là trường hợp đơn giản nhất ở cấp document layout.

Sang M2, layout bắt đầu đa dạng hơn:

- **166 documents** thuộc dạng `1T1P`
- **128 documents** thuộc dạng `2T1P`, tức hai tables trên cùng một page
- **36 documents** thuộc dạng `1T2P`, tức một logical table kéo dài qua hai pages

Ba nhóm trên cộng lại đúng 330 M2 documents.

Với **`2T1P`**, một page có thể chứa nhiều table regions độc lập. Vì vậy, table localization không thể dừng lại sau khi tìm thấy region đầu tiên mà cần phát hiện đầy đủ các bảng và giữ đúng thứ tự xuất hiện của chúng trên page.

Với **`1T2P`**, table region ở mỗi page chỉ biểu diễn một phần của cùng một logical table. Vì vậy, kết quả ở hai page cần được giữ trong cùng document context để có thể hợp nhất về sau, thay vì được xuất thành hai tables độc lập.

Điểm cần phân biệt là **document có hai pages không đồng nghĩa với một table kéo dài qua hai pages**. Trong toàn bộ dataset, một two-page document vẫn có thể chứa các tables độc lập ở từng page. Tuy nhiên, trong phạm vi M2, toàn bộ 36 trường hợp `1T2P` đều thuộc nhóm long-table continuation. Chi tiết về pattern lặp header và cách hai page được hợp nhất sẽ được kiểm tra riêng trong phần cross-page continuation.

**[CHÈN HÌNH 2.3: Một ảnh `1T1P`, một ảnh `2T1P` và hai ảnh page 1, page 2 của một document `1T2P`]**

*Hình 2.3. Ba document-layout patterns xuất hiện trong M1 và M2.*

Kết quả trên cho thấy sự thay đổi từ M1 sang M2 không chỉ nằm trong cấu trúc của từng table. **Bố cục ở cấp document cũng trở thành một phần của bài toán.** Vì vậy, quá trình xử lý cần phân biệt hai cấp:

- **Page level:** xác định số lượng table regions và thứ tự của chúng trên mỗi page.
- **Document level:** giữ quan hệ giữa các table regions ở nhiều pages để có thể hợp nhất các phần thuộc cùng một logical table.

Insight này tạo ra một yêu cầu kiến trúc ở mức cao: table localization được thực hiện theo từng page, trong khi kết quả cuối cùng phải được tổng hợp với context của toàn document.

## 2.3.2. Grid Size & Geometry

Sau khi xem document layout, bước tiếp theo là kiểm tra **kích thước grid của từng table có ổn định hay không**. Ở đây, mỗi table được xem là một observation riêng, với số rows và columns được đọc trực tiếp từ label.

Các phân bố cho thấy M1 và M2 đều không có một grid size cố định. Với M1, table có từ **5 đến 7 columns** và **6 đến 9 rows**. M2 lớn hơn rõ rệt, với **7 đến 9 columns** và **11 đến 33 rows**. Median grid cũng tăng từ khoảng **7 × 5** ở M1 lên **15 × 8** ở M2.

**[CHÈN HÌNH 2.4: Phân bố số cột, số hàng và thống kê grid size của M1/M2]**

*Hình 2.4. Phân bố kích thước table cho thấy số hàng và số cột thay đổi ngay bên trong từng difficulty.*

Điểm quan trọng không chỉ là M2 có grid lớn hơn M1. **Ngay trong cùng một difficulty, số rows và columns vẫn thay đổi giữa các tables.** Vì vậy, một fixed grid size không thể đại diện cho toàn bộ M1 hoặc M2.

Biểu đồ `max_columns` ở cấp document cũng cho thấy M1 và M2 không hoàn toàn tách biệt theo số cột. Giá trị 7 columns xuất hiện ở cả hai nhóm, nên chỉ dựa vào difficulty hoặc một kích thước mặc định cũng không đủ để xác định cấu trúc của một table cụ thể.

Từ EDA này, yêu cầu có thể rút ra là: **grid structure cần được xác định cho từng table riêng thay vì gán trước một template cố định**. EDA ở đây mới xác lập yêu cầu đó. Cách tìm các row và column boundaries từ image sẽ được trình bày ở phần Solution.

## 2.3.3. Merge Structure

Sau khi xác định grid size thay đổi giữa các tables, bước tiếp theo là xem các vị trí trong grid có thực sự tương ứng một một với các cell trong bảng hay không. Đây là một khác biệt cấu trúc quan trọng giữa M1 và M2.

Ở **M1**, toàn bộ 325 tables không có horizontal merge hay vertical merge. Vì vậy, mỗi vị trí trong grid có thể được xem là một cell độc lập. Ngược lại, ở **M2**, merge xuất hiện rất phổ biến: **458/458 tables có ít nhất một horizontal merge**, và **422/458 tables có ít nhất một vertical merge**.

**[CHÈN HÌNH 2.5: Merge prevalence ở M1/M2 và minh họa Atomic Grid → Logical Table]**

*Hình 2.5. Merge structure cho thấy một vị trí trong grid không phải lúc nào cũng tương ứng với một cell độc lập.*

Điều này dẫn tới một hệ quả quan trọng. Các row và column boundaries chỉ xác định được **atomic grid**, tức lưới hình học cơ sở của bảng. Trong M1, mỗi atomic cell cũng chính là một logical cell. Nhưng trong M2, một logical cell có thể chiếm nhiều atomic positions do horizontal hoặc vertical merge.

Vì vậy, **grid reconstruction chưa đủ để mô tả đầy đủ cấu trúc bảng trong M2**. Sau khi xác định atomic grid, hệ thống còn phải phục hồi các merge relationships để nhóm các atomic cells liên quan thành **logical cells**.

Cần lưu ý rằng các marker `[[H]]` và `[[V]]` trong label là **continuation markers**, không phải số lượng merged logical cells. Một logical cell trải qua nhiều vị trí atomic có thể tạo ra nhiều markers, nên các marker này chủ yếu giúp mô tả cách merge được biểu diễn trong output.

Từ EDA này, yêu cầu có thể rút ra là:

**Atomic grid và logical table là hai mức biểu diễn khác nhau.**

Phần Solution sau đó sẽ trình bày cách chuyển từ atomic cells sang logical cells thông qua bước merge reconstruction.

## 2.3.4. Content Characteristics

EDA cho thấy **độ dài text trong cell gần như ổn định giữa các difficulty**. Median text length đều khoảng **5 ký tự**, còn P95 chỉ dao động từ **15 đến 17**, nên sự gia tăng difficulty không đi kèm với việc cell text dài hơn đáng kể.

Điểm khác biệt đáng chú ý hơn là **multiline content**. M1 không có multiline cell, trong khi M2 có multiline rate khoảng **0,9% ở cấp cell**. Tuy tỷ lệ này nhỏ, multiline vẫn xuất hiện trong toàn bộ M2 documents, nên hệ thống không thể bỏ qua trường hợp một logical cell chứa nhiều dòng text.

**[CHÈN HÌNH 2.6: Bảng content statistics và ví dụ một multiline cell]**

*Hình 2.6. Multiline xuất hiện thưa ở cấp cell nhưng hiện diện trong toàn bộ M2 documents.*

Với `escaped pipe`, M1 và M2 đều có tỷ lệ **0%**, trong khi feature này chỉ xuất hiện từ M3 trở đi.

## 2.3.5. M2 Header Grammar

EDA ở cấp **page-table** cho thấy phần header của M2 có một pattern rất ổn định. Trên toàn bộ **494 M2 training page-tables** được kiểm tra, ba hàng đầu đều tuân theo cùng một grammar: row 0 span toàn bộ columns, row 1 chia thành hai group tại vị trí `cols // 2`, và row 2 gồm các leaf headers riêng lẻ. Không có exception nào trong tập quan sát này.

**[CHÈN HÌNH 2.7: header M2 thật + bảng evidence 494/494]**

*Hình 2.7. Tất cả 494 M2 training page-tables được quan sát đều chia sẻ cùng một three-row header grammar.*

Kết quả này cho thấy horizontal merge trong header của M2 không phải một cấu trúc bất kỳ. Trong phạm vi training set, nó tuân theo một **dataset-specific grammar** nhất quán. Vì vậy, grammar này có thể được xem như một giả thuyết ưu tiên khi khôi phục header M2 trong phần Solution.

Tuy nhiên, kết luận này được rút ra khi **đã biết table thuộc M2**, nên nó không thay thế cho bước nhận diện đúng loại table trong pipeline.

## 2.3.6. Bold Grammar

EDA cho thấy **bold formatting trong M2 phụ thuộc nhất quán vào structural role và page context**. Sau khi loại empty cells khỏi audit, ba header rows đầu tiên đều có bold rate **100%**, trong khi các body rows có bold rate **0%**. Điều này cho thấy formatting của phần header khớp với structural grammar đã quan sát ở mục trước.

Sự khác biệt ở last row chỉ trở nên rõ ràng khi tách theo page context. Trong các one-page tables, **422/422 terminal rows** đều bold. Với cross-page tables, **36/36 last rows của page 1** không bold vì bảng còn tiếp tục ở trang sau, trong khi **36/36 terminal rows của page 2** đều bold.

**[CHÈN HÌNH 2.8: Bold grammar theo structural role và last-row context]**

*Hình 2.8. Bold formatting trong M2 thay đổi theo structural role và page context.*

Kết quả này cho thấy, trong **M2 training set**, bold có thể được mô tả bằng một **dataset-specific formatting grammar**. Ba header rows và terminal row đều bold, trong khi body rows và last row của page 1 đang tiếp tục đều không bold. Điều này tạo cơ sở để xem row role và page context là tín hiệu chính khi khôi phục formatting, với điều kiện các structural roles được xác định đúng từ ảnh.

Sau khi tách page context, label-level EDA không còn cho thấy terminal row nào cần được phân biệt bằng stroke score. Vì vậy, image-based threshold chưa được chứng minh là cần thiết đối với các pattern đã quan sát; vai trò của nó như một fallback cần được đánh giá riêng trong phần Solution.

## 2.3.7. Cross-Page Continuation Pattern

EDA tiếp tục kiểm tra các **M2 documents có hai pages** để xác định cách một logical table được tiếp tục qua page boundary. Trong toàn bộ **36 M2 two-page training documents** được quan sát, hai page luôn có cùng số columns và page 2 luôn lặp lại **đúng cùng một three-row header block** đã được xác lập ở mục trước.

Khi giữ nguyên toàn bộ page 1 và nối phần body của page 2 sau khi bỏ header block lặp lại, document label được khôi phục chính xác trong **36/36** trường hợp.

**[CHÈN HÌNH 2.9: Page 1, Page 2, repeated three-row header block và rule `page1 + page2[3:]`]**

*Hình 2.9. Trong toàn bộ 36 M2 two-page training documents, page 2 lặp lại đúng three-row header block trước khi tiếp tục phần body của cùng một logical table.*

Kết quả này cho thấy, trong phạm vi M2 training set, page 2 không được xử lý như một table độc lập. Thay vào đó, nó là phần tiếp nối của cùng một logical table, với một header block ba hàng được lặp lại ở đầu page mới.

Điều này tạo ra một **dataset-specific continuation grammar** cho bước cross-page stitching. Tuy nhiên, việc áp dụng grammar này trong inference vẫn phụ thuộc vào khả năng nhận diện đúng M2 two-page pattern và ghép đúng hai page-table tương ứng từ ảnh.

## 2.3.8. Page Appearance & Alignment

Ngoài structure và formatting, EDA cũng xem xét mức độ ổn định của hình ảnh ở cấp page. Với target M1 và M2, các trang nhìn chung có bố cục khá ổn định và các đường ngang của bảng tập trung gần phương ngang.

**[CHÈN HÌNH 2.10: Phân bố góc gần ngang theo difficulty]**

*Hình 2.10. M1 và M2 nhìn chung có mức skew thấp hơn so với các difficulty cao hơn.*

Kết quả này cho thấy **skew không phải một đặc điểm nổi bật trong M1/M2 training data**. Vì vậy, EDA không đặt deskew như một yêu cầu trung tâm của target distribution.

Điều này không có nghĩa mọi ảnh đều hoàn toàn thẳng hoặc deskew không bao giờ hữu ích. Nó chỉ cho thấy alignment của M1/M2 tương đối ổn định trong dữ liệu quan sát được. Các bước xử lý tăng robustness cho những trường hợp ảnh bị nghiêng có thể được xem xét riêng trong phần Solution.

# 3. Solution Architecture

Từ các yêu cầu rút ra trong EDA, solution được thiết kế thành một pipeline đi từ **ảnh tài liệu** đến **bảng Markdown có cấu trúc**.

Ở mức tổng thể, hệ thống cần giải quyết bốn bài toán liên tiếp:

1. **Tìm bảng và phục hồi cấu trúc**
    Ảnh được xử lý để làm rõ các đường kẻ, sau đó xác định vị trí từng bảng và cấu trúc hàng, cột bên trong.
2. **Đọc nội dung trong từng ô**
    Sau khi cấu trúc bảng đã được xác định, nội dung của từng ô được crop và nhận dạng bằng OCR.
3. **Khôi phục thông tin không nằm trong text thuần**
    Hệ thống tiếp tục xử lý các đặc điểm như merged cells, multiline content, bold formatting và quan hệ giữa các phần của bảng nằm trên nhiều pages.
4. **Chuyển kết quả thành Extended Markdown**
    Cuối cùng, toàn bộ thông tin về text, cấu trúc và formatting được kết hợp để tạo output đúng định dạng của bài toán.

**[CHÈN HÌNH 3.1: Overall Solution Architecture]**

*Hình 3.1. Tổng quan pipeline từ document images đến Extended Markdown.*

Trong pipeline này, **Table Detection & Structure Reconstruction** là phần nền tảng. Nếu vị trí bảng, hàng, cột hoặc merged cells được phục hồi sai thì OCR đúng text vẫn chưa đủ để tạo lại bảng chính xác. Vì vậy, solution trước tiên tập trung xây dựng đúng cấu trúc bảng, sau đó mới gắn content và formatting vào cấu trúc đó.
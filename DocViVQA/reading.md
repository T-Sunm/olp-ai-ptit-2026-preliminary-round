# Tutorial: Xây dựng hệ thống hỏi đáp trên ảnh tài liệu (Olympic AI)

**Tác giả:** Trần Quang Minh, Đinh Quang Vinh

## I. Giới thiệu

Trong nhiều hoạt động hằng ngày, từ xử lý hồ sơ hành chính, kiểm tra hóa đơn đến tổng hợp báo cáo và biểu mẫu, con người thường phải đọc tài liệu để tìm kiếm và lấy ra thông tin cần thiết. Tuy nhiên, người dùng thường chỉ quan tâm đến một phần cụ thể, chẳng hạn tổng chỉ tiêu của hai phòng ban, một giá trị trong bảng hay mục có số liệu lớn nhất. Khi số lượng tài liệu tăng lên, việc tự mở từng trang, dò đúng vị trí rồi tính toán hoặc so sánh thủ công sẽ trở nên tốn thời gian, vì vậy một cách tiếp cận cho phép người dùng hỏi trực tiếp và nhận lại thông tin cần thiết sẽ trở nên hữu ích hơn.

Từ nhu cầu đó hình thành bài toán **Document Visual Question Answering (Document VQA)**. Hệ thống nhận vào một tài liệu cùng câu hỏi về nội dung bên trong và cần đưa ra câu trả lời phù hợp. Khác với hỏi đáp trên văn bản thuần túy, thông tin trong tài liệu còn được thể hiện qua cách nội dung được bố trí trên trang, chẳng hạn các hàng và cột trong bảng. Vì nhiều tài liệu tồn tại dưới dạng ảnh chụp hoặc bản scan, **Optical Character Recognition (OCR)** thường được sử dụng để chuyển chữ trong ảnh thành văn bản số kèm vị trí tương ứng trên trang, tạo đầu vào để hệ thống tiếp tục xác định thông tin liên quan và trả lời câu hỏi.

> **Hình 1:** Minh họa quá trình trả lời câu hỏi trên tài liệu từ OCR đến đáp án và evidence.

Trong challenge lần này của **Olympic AI PTIT 2026**, bài toán Document Visual Question Answering được đặt trong bối cảnh các tài liệu có nhiều bảng biểu và thông tin được tổ chức theo bố cục. Với mỗi câu hỏi, hệ thống không chỉ cần đưa ra đáp án mà còn phải chỉ ra những vùng trên tài liệu đã được sử dụng làm bằng chứng. Điều này khiến bài toán gần hơn với nhu cầu thực tế, nơi một câu trả lời hữu ích không chỉ cần đúng mà còn cần cho biết nó được lấy từ đâu.

## II. Phân tích đề thi

### 1. Thể lệ và yêu cầu của cuộc thi

Trong challenge Document Visual Question Answering của Olympic AI PTIT 2026, mỗi mẫu dữ liệu gồm một tài liệu dạng ảnh cùng các câu hỏi liên quan đến nội dung bên trong. Hệ thống cần trả lời đúng câu hỏi, đồng thời xác định những vùng trên tài liệu đã được sử dụng làm bằng chứng cho câu trả lời.

#### Đầu vào và đầu ra của bài toán

Đầu vào của mỗi mẫu gồm một tài liệu có từ **1 đến 2 trang ảnh**, kết quả OCR tương ứng với từng trang và các câu hỏi về nội dung tài liệu. OCR cung cấp cả nội dung văn bản và **bounding box** của từng khối, nhờ đó hệ thống có thể biết một đoạn text xuất hiện ở đâu trên trang. Mỗi tài liệu có **10 câu hỏi**, trong đó đáp án có thể là văn bản xuất hiện trực tiếp trong tài liệu hoặc một giá trị số cần được tính toán từ dữ liệu trong bảng.

Với mỗi câu hỏi, hệ thống cần trả về hai thành phần:

- **Answer:** Câu trả lời cuối cùng.
- **Evidence:** Một hoặc nhiều vùng trên tài liệu chứa những thông tin được sử dụng để tạo ra câu trả lời.

Như vậy, bài toán không chỉ yêu cầu tìm đúng đáp án mà còn yêu cầu xác định được nguồn thông tin dẫn đến đáp án đó.

#### Cấu trúc một mẫu dữ liệu

Một document bao gồm ảnh của từng trang, OCR tương ứng và 10 câu hỏi được định danh bằng `question_id`. Riêng ở tập training, ban tổ chức cung cấp thêm các annotation phục vụ quá trình phân tích và xây dựng lời giải, gồm:

- đáp án đúng
- loại câu hỏi
- `reasoning_type`
- evidence tương ứng
- `cell_annotations` mô tả các ô trong bảng theo hàng, cột, nội dung và vị trí

Các thành phần này có thể được hình dung trực quan như trong hình dưới đây. Phần bên trái là những dữ liệu hệ thống nhận được như ảnh tài liệu, OCR kèm bounding box và câu hỏi. Phần bên phải là các annotation chỉ có ở training, bao gồm answer, reasoning type, evidence và thông tin chi tiết của các cell.

> **Hình 2:** Cấu trúc một mẫu dữ liệu trong training set.

#### Cấu trúc file nộp

Kết quả dự đoán được lưu trong file `predictions.jsonl`, trong đó mỗi dòng tương ứng với một câu hỏi:

```json
{
  "question_id": "...",
  "answer": "...",
  "evidence": [
    {
      "page": 1,
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

Sau đó, file `predictions.jsonl` được đóng gói thành file ZIP để nộp lên hệ thống chấm.

Trong `bbox = [x1, y1, x2, y2]`, cặp `(x1, y1)` là góc trên bên trái và `(x2, y2)` là góc dưới bên phải của vùng. Các tọa độ được chia cho chiều rộng hoặc chiều cao của trang nên có giá trị từ `0` đến `1`.

#### Cách tính điểm

Điểm của mỗi câu hỏi được tính từ hai thành phần:

```text
Question Score = 0.85 × ANLS + 0.15 × Evidence-F1
```

Trong đó, **Average Normalized Levenshtein Similarity (ANLS)** đo mức độ giống nhau giữa câu trả lời dự đoán và đáp án đúng dựa trên số ký tự cần thêm, xóa hoặc thay thế. **Evidence-F1** đánh giá các vùng bằng chứng được hệ thống xác định. Như vậy, phần trả lời chiếm **85%** tổng điểm của mỗi câu hỏi, trong khi phần bằng chứng đóng góp **15%**.

Để tính Evidence-F1, trước hết cần xác định một vùng bằng chứng dự đoán có khớp với vùng ground truth hay không. Việc so khớp này sử dụng **Intersection over Union (IoU)**, là tỷ lệ giữa diện tích phần giao và diện tích phần hợp của hai bounding box.

> **Hình 3:** Minh họa Intersection over Union giữa Predicted và Ground Truth Bounding Box.

Trong challenge, một vùng bằng chứng dự đoán được xem là khớp khi:

- nằm trên cùng trang với vùng ground truth
- có **IoU ≥ 0.5**

Từ các cặp vùng được xác định là khớp, hệ thống tính **precision**, tức tỷ lệ vùng dự đoán thực sự đúng, và **recall**, tức tỷ lệ vùng đúng đã được tìm thấy. Hai giá trị này được kết hợp thành Evidence-F1. Vì vậy, một lời giải tốt không chỉ cần trả lời đúng câu hỏi mà còn cần xác định tương đối chính xác vị trí của những thông tin đã được sử dụng để đưa ra câu trả lời.

#### Public test và private test

Dữ liệu của cuộc thi được chia thành ba phần:

| Tập dữ liệu | Documents | Pages | Questions |
|---|---:|---:|---:|
| Training set | 1,100 | 1,426 | 11,000 |
| Public test | 100 | 131 | 1,000 |
| Private test | 200 | 265 | 2,000 |

Public test được sử dụng để cung cấp phản hồi trong quá trình thi, giúp các đội quan sát kết quả và điều chỉnh phương pháp. Private test được dùng để xác định kết quả cuối cùng, vì vậy lời giải cần hoạt động ổn định trên cả dữ liệu đã dùng để phát triển lẫn những tài liệu chưa được quan sát trước đó.

### 2. Dữ liệu

Dữ liệu của challenge được tổ chức theo từng document, mỗi document gồm một đến hai trang ảnh và đi kèm 10 câu hỏi. Bộ dữ liệu được chia thành Training set, Public test và Private test. Phần **Exploratory Data Analysis (EDA)**, hay phân tích khám phá dữ liệu, dưới đây được thực hiện trên Training set nhằm tìm ra các quy luật làm cơ sở xây dựng lời giải.

#### Cấu trúc dữ liệu

Ở cả training và test, hệ thống đều nhận được ảnh tài liệu, kết quả OCR kèm vị trí của các khối văn bản và các câu hỏi liên quan đến document. Riêng Training set cung cấp thêm các annotation như đáp án đúng, loại suy luận, vùng bằng chứng và thông tin chi tiết của các ô trong bảng.

| Thành phần | Training | Test |
|---|:---:|:---:|
| Ảnh tài liệu | ✓ | ✓ |
| OCR và Bounding Box | ✓ | ✓ |
| Câu hỏi | ✓ | ✓ |
| Answer và Evidence | ✓ | × |
| Cell annotations | ✓ | × |

Một mẫu training vì vậy có thể được nhìn như sự kết hợp giữa **ảnh, OCR, câu hỏi** và các **nhãn huấn luyện**. OCR cung cấp nội dung chữ cùng bounding box chuẩn hóa của từng khối, còn phần nhãn bổ sung đáp án, loại suy luận, evidence và cấu trúc các ô trong bảng. Nhờ đó, tập training không chỉ cho biết đáp án cuối cùng mà còn cho phép đối chiếu câu hỏi với các vùng và ô dữ liệu liên quan.

#### Phân bố các loại suy luận

Các câu hỏi trong Training set được chia thành tám loại suy luận chính: **Lookup, Sum, Count, Argmax, Argmin, Compare, Visual Bold Lookup** và **Cross-page Sum**.

Phân bố cho thấy phần lớn dữ liệu tập trung vào các thao tác có cấu trúc trên bảng, trong khi Visual Bold Lookup và đặc biệt Cross-page Sum chỉ chiếm tỷ lệ nhỏ. Nhìn tổng thể, khoảng **95% câu hỏi** có thể quy về các thao tác có cấu trúc trên bảng.

#### Các quy luật đáng chú ý từ EDA

EDA cho thấy vị trí của các ô trong bảng khá ổn định. Các cell thuộc cùng hàng hoặc cùng cột thường thẳng hàng, còn header thường nằm ngay phía trên các cell dữ liệu tương ứng. Điều này cho thấy cấu trúc bảng vẫn được phản ánh khá rõ qua bounding box, dù OCR không biểu diễn trực tiếp quan hệ hàng và cột.

> **Hình 4:** Các quy luật về bố cục và sự thẳng hàng trong bảng.

Bên cạnh đó, cách đặt câu hỏi cũng có tính lặp lại tương đối cao. Nhiều loại suy luận thường đi kèm những cụm từ đặc trưng và ít dùng chung với loại khác, trong khi Lookup có cách diễn đạt đa dạng hơn các nhóm còn lại.

| Loại suy luận | Cụm từ đặc trưng | Trong loại này | Ngoài loại này |
|---|---|---:|---:|
| argmax | lớn nhất, nào có | 100% | ~0% |
| argmin | nhỏ nhất, nào có | 100% | ~0% |
| compare | với dòng có, so sánh tại bảng | 100% | 0% |
| count | có bao nhiêu dòng | 100% | 0% |
| sum | tổng, hai dòng có | 100% | 0% |
| lookup | tại bảng, ghi ... bằng bao nhiêu | 62% | 23% |
| visual_bold_lookup | in đậm, chữ, ảnh | 100% | 0% |
| cross_page_sum | cộng với, kết quả | 100% | 0% |

> **Hình 5:** Tính lặp lại trong cách đặt câu hỏi theo từng loại suy luận.

Ngoài những quy luật phổ biến, dataset còn có một số trường hợp đặc biệt. Với **Cross-page Sum**, phép xử lý vẫn là cộng nhưng các giá trị cần dùng có thể nằm ở nhiều trang khác nhau của cùng document.

> **Hình 6:** Ví dụ câu hỏi Cross-page Sum với dữ liệu nằm trên nhiều trang.

Trong khi đó, **Visual Bold Lookup** là trường hợp mà OCR không đủ, vì thuộc tính in đậm không được biểu diễn trong text hay bounding box. Do đó ảnh gốc vẫn chứa một phần thông tin cần thiết để trả lời câu hỏi.

> **Hình 7:** Ví dụ Visual Bold Lookup cần khai thác thông tin trực tiếp từ ảnh.

Tổng hợp các quan sát trên cho thấy dataset có mức độ cấu trúc khá rõ ở cả bố cục bảng lẫn cách đặt câu hỏi, đồng thời vẫn tồn tại một số trường hợp yêu cầu kết hợp thông tin giữa nhiều trang hoặc khai thác trực tiếp tín hiệu từ ảnh. Đây là cơ sở để lựa chọn hướng triển khai phù hợp ở phần tiếp theo.

### 3. Hướng triển khai

Từ kết quả EDA có thể thấy bài toán có mức độ cấu trúc khá rõ. Phần lớn câu hỏi xoay quanh một số thao tác cụ thể trên bảng, cách diễn đạt có nhiều mẫu lặp lại, còn vị trí của các OCR block vẫn giữ được nhiều thông tin về bố cục tài liệu. Vì vậy, lời giải được thiết kế theo hướng khai thác trực tiếp những đặc điểm này thay vì xử lý toàn bộ tài liệu như một chuỗi văn bản phẳng.

#### Từ EDA đến lựa chọn hướng xử lý

Lời giải kết hợp ba nguồn thông tin chính là **text, vị trí và ảnh**. Text cung cấp nội dung của từng OCR block, còn bounding box cho biết vị trí và quan hệ không gian giữa các block trên trang. Hai nguồn này được dùng để xử lý phần lớn câu hỏi, từ xác định đúng vùng bảng đến tìm hàng và ô dữ liệu liên quan.

Ảnh gốc chỉ được sử dụng khi thông tin cần trả lời không được thể hiện trong OCR. Chẳng hạn với Visual Bold Lookup, OCR vẫn cung cấp text và bounding box của các dòng liên quan nhưng không lưu thông tin về độ đậm của chữ. Khi đó, lời giải trước tiên dùng nội dung và vị trí để tìm các **hàng ứng viên**, tức những hàng có khả năng chứa đáp án, rồi mới quay lại ảnh gốc để xác định hàng nào có nét chữ đậm hơn.

Với những câu hỏi có dữ liệu nằm trên nhiều trang, hướng xử lý cũng không thay đổi hoàn toàn. Hệ thống vẫn truy xuất các giá trị cần thiết theo cùng cách như trên một trang, nhưng mở rộng phạm vi tìm kiếm sang từng trang liên quan trước khi thực hiện phép tính.

Quy trình tổng quát trong tài liệu gồm:

```text
OCR được cung cấp ──> Các khối văn bản và vị trí ──> Khôi phục bảng
                                                          │
                                                          v
                                                  Các hàng và ô ứng viên
                                                          │
Ảnh tài liệu ────────────────────────────────> Xác định hàng in đậm
                                                          │
Câu hỏi ──> Trích xuất yêu cầu và điều kiện ──> Chọn phép suy luận
                                                          │
                   ┌──────────────────────────────────────┼──────────────────────────────────────┐
                   v                                      v                                      v
             Tra cứu trực tiếp                    Tổng hợp dữ liệu                    Xếp hạng/so sánh
                   └──────────────────────────────────────┼──────────────────────────────────────┘
                                                          v
                                                  Đáp án + bằng chứng
```

#### Từ câu hỏi đến Structured Intent

Bước đầu tiên là chuyển câu hỏi từ ngôn ngữ tự nhiên thành **Structured Intent**, một biểu diễn có cấu trúc chứa những thông tin mà các bước phía sau cần sử dụng. Các thông tin này gồm loại suy luận, trang, bảng, cột cần lấy giá trị và những điều kiện dùng để xác định hàng.

Ví dụ, với câu hỏi yêu cầu tính tổng giá trị **Tuyển mới** của hai phòng ban cụ thể, hệ thống cần nhận ra đây là một phép **Sum**, xác định đúng trang và bảng, chọn Tuyển mới làm cột cần lấy giá trị, sau đó tách các điều kiện về phòng ban và định biên để tìm các hàng liên quan.

Do cách đặt câu hỏi trong dataset có nhiều mẫu lặp lại, lời giải ưu tiên phân tích dựa trên các mẫu câu thường gặp. Khi câu hỏi không khớp hoàn toàn, hệ thống thử dùng một số quy tắc bổ sung để nhận diện loại suy luận và lấy lại các thông tin đơn giản. Cơ chế này hỗ trợ chủ yếu các câu hỏi trên một trang. Cross-page Sum và Visual Bold Lookup vẫn phụ thuộc vào các mẫu câu chuyên biệt.

#### Khôi phục cấu trúc bảng từ OCR và vị trí

OCR chỉ cung cấp text và bounding box của từng block, chứ không biểu diễn trực tiếp block nào thuộc cùng hàng, header (tiêu đề cột) nào tương ứng với cell (ô dữ liệu) nào hay đâu là phạm vi của từng bảng. Vì vậy, lời giải giữ lại toàn bộ thông tin vị trí của OCR để khôi phục các quan hệ này.

Để khôi phục cấu trúc bảng, hệ thống trước tiên xác định vùng bảng cần xử lý. Những OCR block có cùng vị trí mép trên `y1` được gom thành các hàng vật lý. Khi một cell kéo dài qua nhiều hàng, hệ thống dùng thêm điểm đại diện `row_y` để dựng lại hàng logic đầy đủ. Quan hệ theo cột được xác định dựa trên vị trí tâm theo chiều ngang, tức trục X, của header.

Trong thực tế, một OCR block không phải lúc nào cũng tương ứng chính xác với một cell hoặc một hàng trong bảng. Nội dung có thể bị tách thành nhiều block hoặc một block có thể kéo dài qua nhiều hàng, vì vậy hệ thống cần điều chỉnh lại cách nhóm các block để khôi phục được những hàng dữ liệu hoàn chỉnh trước khi truy xuất.

Hai quy tắc chính được minh họa trong tài liệu:

```text
header x-range = [0.23, 0.35]
header center-X = (x1 + x2) / 2 ≈ 0.29
→ cell.x1 ≤ header center-X ≤ cell.x2
→ same column

cell.y1 ≤ row_y ≤ cell.y2
→ same row
```

Với hàng, các block có vị trí Y phù hợp được nhóm vào cùng một dòng dữ liệu. Với cột, sau khi xác định một header như **Hồ sơ nhận**, hệ thống lấy tâm theo trục X của header làm mốc và tìm cell có vùng X bao quanh vị trí đó. Nhờ vậy, mỗi OCR block không chỉ được nhận diện về mặt nội dung mà còn được gắn với đúng vị trí trong cấu trúc bảng.

#### Truy xuất dữ liệu trước, suy luận sau

Sau khi câu hỏi đã được chuẩn hóa và cấu trúc bảng được khôi phục, hệ thống mới truy xuất những dữ liệu cần thiết. Các điều kiện trong Structured Intent được dùng để tìm đúng hàng, sau đó cột cần lấy giá trị được dùng để xác định cell tương ứng.

Các loại suy luận khác nhau chủ yếu ở cách xử lý sau khi dữ liệu đã được truy xuất:

- **Lookup:** tìm một hàng thỏa điều kiện rồi lấy trực tiếp giá trị ở cột được yêu cầu.
- **Count:** tìm tất cả các hàng thỏa điều kiện rồi đếm số lượng.
- **Sum:** xác định các hàng tương ứng với từng nhóm điều kiện, lấy giá trị ở cùng một cột rồi cộng lại.
- **Compare:** truy xuất hai hàng cần so sánh, lấy giá trị ở cột được chỉ định rồi chọn đối tượng phù hợp với điều kiện lớn hơn hoặc nhỏ hơn trong câu hỏi.
- **Argmax và Argmin:** xét các giá trị trong một cột để tìm hàng có giá trị lớn nhất hoặc nhỏ nhất, sau đó lấy thông tin cần trả về từ chính hàng đó.
- **Cross-page Sum:** vẫn sử dụng cách truy xuất tương tự Sum, nhưng các giá trị cần tính được lấy từ những trang khác nhau trước khi cộng lại.
- **Visual Bold Lookup:** vẫn bắt đầu bằng nội dung và vị trí để xác định các hàng ứng viên, sau đó mới dùng ảnh gốc để chọn hàng có nét chữ đậm hơn.

Điểm chung của các nhánh xử lý là phần suy luận chỉ bắt đầu sau khi phạm vi dữ liệu liên quan đã được xác định. Nhờ đó, mỗi loại câu hỏi chỉ cần làm việc với những hàng và ô thực sự cần thiết thay vì xử lý toàn bộ document cùng lúc.

#### Tạo Evidence từ câu hỏi và kết quả truy xuất

Evidence không được lấy từ toàn bộ hàng hay toàn bộ bảng. Hệ thống chỉ giữ lại các OCR block tạo thành đường dẫn từ câu hỏi đến đáp án, gồm các ô chứa đối tượng hoặc điều kiện được nhắc đến trong câu hỏi và các ô giá trị trực tiếp tham gia vào phép tính, so sánh hoặc kết quả trả về.

Ví dụ, với câu hỏi tính tổng **Tuyển mới** của hai dòng có Phòng ban **Kinh doanh** và **Kế toán**, hệ thống truy xuất hai cặp dữ liệu `Kinh doanh -> 3` và `Kế toán -> 5`. Evidence khi đó gồm bốn ô `Kinh doanh`, `3`, `Kế toán` và `5`, vì đây là những thông tin cần thiết để kiểm tra lại đáp án `8`.

Quy tắc chọn evidence cho từng loại câu hỏi được tóm tắt như sau:

| Loại câu hỏi | Các ô được đưa vào evidence |
|---|---|
| Lookup | Ô điều kiện xác định hàng và ô chứa đáp án |
| Count | Ô điều kiện của các hàng được đếm |
| Sum | Ô điều kiện của hai hàng và hai ô giá trị được cộng |
| Compare | Ô điều kiện và ô giá trị của cả hai hàng được so sánh |
| Argmax và Argmin | Các ô tối thiểu để xác định hàng thắng và ô chứa giá trị cực trị |
| Cross-page Sum | Ô điều kiện và ô giá trị của từng toán hạng trên mỗi trang |
| Visual Bold Lookup | Ô điều kiện của cả hai hàng ứng viên và ô đáp án của hàng in đậm |

Với Argmax và Argmin, ô chứa đáp án đôi khi chưa đủ để xác định duy nhất một hàng. Chẳng hạn, nếu bảng có hai dòng cùng mang tên **Kế toán** nhưng có Định biên lần lượt là `30` và `34`, evidence cần chứa thêm Định biên để phân biệt. Nếu dòng `Kế toán -> 30` có Tuyển mới lớn nhất là `5`, evidence tương ứng sẽ gồm `Kế toán`, `30` và `5`.

Với Visual Bold Lookup, cả hai hàng ứng viên đều được dùng để so sánh kiểu chữ nên điều kiện của cả hai phải xuất hiện trong evidence, dù đáp án cuối cùng chỉ được lấy từ hàng in đậm. Các header chỉ hỗ trợ định vị cột và các vùng không trực tiếp chứng minh câu trả lời sẽ không được đưa vào kết quả, qua đó hạn chế bounding box dư thừa làm giảm precision.

### 4. Kiến thức cần có

Đối với challenge này, người tham gia cần có nền tảng về xử lý tài liệu, thị giác máy tính và các kỹ thuật xử lý dữ liệu có cấu trúc. Việc nắm được những kiến thức này sẽ giúp quá trình phân tích đề, lựa chọn hướng tiếp cận và xây dựng lời giải trở nên thuận lợi hơn.

Về mặt lý thuyết, một số nhóm kiến thức đáng chú ý gồm:

- **Optical Character Recognition và xử lý tài liệu:** hiểu cách văn bản được nhận diện từ ảnh, cách vị trí của nội dung được biểu diễn và cách khai thác bố cục của tài liệu.
- **Computer Vision cơ bản:** nắm các kỹ thuật xử lý ảnh như phân ngưỡng sáng tối, cắt vùng ảnh, trích xuất đặc trưng và các mô hình mạng nơ-ron tích chập (CNN) phổ biến.
- **Xử lý ngôn ngữ tự nhiên cơ bản:** có khả năng phân tích câu hỏi, nhận diện ý định và trích xuất các thông tin cần thiết từ câu.
- **Xử lý dữ liệu có cấu trúc:** hiểu cách làm việc với bảng, hàng, cột, điều kiện lọc, các phép tổng hợp và so sánh.
- **Kỹ thuật đánh giá mô hình:** nắm các metric phổ biến cho bài toán hỏi đáp, phát hiện vùng và so khớp kết quả.

Về mặt thực hành, người tham gia nên có nền tảng **Python** và làm quen với các thư viện như **NumPy, OpenCV, PIL/Pillow và PyTorch** để xử lý dữ liệu và xây dựng mô hình.

## III. Xây dựng lời giải

Phần này hiện thực hóa hướng tiếp cận đã trình bày ở trên thành một quy trình hoàn chỉnh. Thay vì xử lý tài liệu như một chuỗi văn bản phẳng, hệ thống lần lượt chuẩn hóa dữ liệu đầu vào, phân tích câu hỏi, truy xuất các ô liên quan, thực hiện phép suy luận và tạo ra answer cùng evidence.

### Chuẩn bị thực hành

Trước khi bắt đầu, tải bộ dữ liệu được đính kèm trong phần Phụ lục và giải nén vào `DocViVQA/data/`. Sau khi giải nén, thư mục này cần chứa ba tập `training_set`, `public_test` và `private_test`.

Notebook chính sử dụng NumPy, OpenCV, Pillow, PyTorch và Torchvision. Khi chạy local, cần mở `submission_pipeline.ipynb` với `DocViVQA/notebooks` làm working directory để các đường dẫn tương đối tới `data`, `artifacts` và `outputs` được xác định đúng.

```text
DocViVQA/
├── data/
│   ├── training_set/
│   ├── public_test/
│   └── private_test/
├── artifacts/models/
├── notebooks/
├── outputs/
└── scripts/
```

Để chạy lại lời giải, thực hiện theo thứ tự sau:

1. Tải và giải nén `data.zip` vào `DocViVQA/data/`.
2. Mở `train_bold_pair_colab.ipynb` trên Colab, chọn GPU và chạy toàn bộ notebook. Sau đó tải file trọng số đã huấn luyện `bold_pair_resnet18.pt` về `DocViVQA/artifacts/models/`.
3. Mở `submission_pipeline.ipynb` từ thư mục `DocViVQA/notebooks/`, đặt `SPLIT = "training_set"` và chạy lần lượt các cell để sinh prediction.
4. Từ thư mục gốc của repository, chạy lệnh sau để đánh giá kết quả:

```powershell
python DocViVQA/scripts/evaluate_predictions.py DocViVQA/outputs/predictions_training_set.jsonl
```

Script xuất kết quả theo từng reasoning type và lưu riêng những câu chưa đạt điểm tối đa để tiếp tục phân tích. Khi chạy trên test, chỉ cần đổi `SPLIT` thành `public_test` hoặc `private_test`. Hai tập này không có nhãn để đánh giá cục bộ.

### Biểu diễn tài liệu từ dữ liệu đầu vào

Mỗi document có một file OCR và một hoặc hai ảnh trang. Bước đầu tiên đọc `manifest.jsonl`, tức file liệt kê ID cùng đường dẫn OCR và ảnh của từng document, rồi gom các OCR block vào một biểu diễn chung. Kết quả cần giữ được text, bounding box, số trang và đường dẫn ảnh để các bước sau có thể sử dụng cùng một đầu vào.

```python
@dataclass
class DocumentLayout:
    document_id: str
    blocks: list[dict]
    image_paths: list[Path] = field(default_factory=list)


def load_split(split_dir):
    manifests = read_jsonl(split_dir / "manifest.jsonl")
    questions = read_jsonl(split_dir / "questions.jsonl")
    layouts = {}

    for manifest in manifests:
        ocr_path = split_dir / manifest["ocr_path"]
        payload = json.loads(ocr_path.read_text(encoding="utf-8"))
        layouts[manifest["id"]] = DocumentLayout(
            document_id=manifest["id"],
            blocks=[block for page in payload["pages"] for block in page["blocks"]],
            image_paths=[split_dir / path for path in manifest["image_paths"]],
        )

    return questions, layouts

# ... Phần đọc JSONL đầy đủ được đính kèm ở Phụ lục
```

`DocumentLayout` gộp các block của nhiều trang vào cùng một danh sách nhưng mỗi block vẫn giữ trường `page`. Nhờ đó, các **solver**, tức những hàm thực hiện việc trả lời câu hỏi, có thể lọc dữ liệu theo trang mà không cần đọc lại file OCR. `image_paths` chưa được dùng ở các nhánh xử lý text, nhưng sẽ được dùng khi giải câu hỏi Visual Bold Lookup.

Kết quả của bước này là danh sách câu hỏi và ánh xạ từ `document_id` đến `DocumentLayout`. Câu hỏi tiếp theo được chuyển thành một yêu cầu có cấu trúc trước khi truy xuất document tương ứng.

### Phân tích câu hỏi thành biểu diễn có cấu trúc (Structured Intent)

Câu hỏi tự nhiên chứa đồng thời loại phép toán, vị trí bảng và các điều kiện lọc. Để các solver không phải tự phân tích lại câu hỏi, hệ thống chuẩn hóa các thông tin này thành `StructuredIntent`.

```python
@dataclass(frozen=True)
class StructuredIntent:
    reasoning_type: str
    template: str | None
    fields: dict
    route_source: str


REQUIRED_FIELDS = {
    "lookup": {"table", "page", "target_column", "condition_pairs"},
    "sum": {"table", "page", "target_column", "condition_pairs"},
    "argmax": {"table", "page", "return_column", "value_column"},
    "visual_bold_lookup": {
        "table", "page", "target_column", "row_condition_groups"
    },
    # ... Danh sách reasoning type đầy đủ được đính kèm ở Phụ lục
}
```

Ví dụ, câu hỏi yêu cầu tính tổng **Tuyển mới** của hai phòng ban được biểu diễn như sau:

```python
StructuredIntent(
    reasoning_type="sum",
    template="sum_two_rows",
    fields={
        "table": 1,
        "page": 1,
        "target_column": "Tuyển mới",
        "condition_pairs": [
            ("Phòng ban", "Kinh doanh"),
            ("Phòng ban", "Kế toán"),
        ],
    },
    route_source="strong_template",
)
```

Trong đó, `reasoning_type` quyết định phép suy luận và `fields` chứa dữ liệu đầu vào cho solver. `template` ghi lại mẫu câu đã khớp, còn `route_source` cho biết intent được tạo từ mẫu câu chắc chắn hay từ quy tắc dự phòng. `condition_pairs` biểu diễn một điều kiện dưới dạng `(tên cột, giá trị)`. Với các phép so sánh hai hàng, các điều kiện được tách thành hai `row_condition_groups` riêng biệt.

#### Nhận diện mẫu câu

Do cách đặt câu hỏi có tính lặp lại cao, hệ thống ưu tiên **regular expression (regex)**, tức các biểu thức mô tả khuôn dạng của câu. Một regex vừa kiểm tra câu hỏi có đúng mẫu hay không, vừa lấy ra các phần cần thiết như số bảng, số trang và tên cột.

```python
PATTERN_CATALOG = {
    "argmax": {
        "argmax_standard": re.compile(
            r"Trong bảng (?P<table>\d+) ở trang (?P<page>\d+), "
            r"(?P<return_column>.+?) nào có "
            r"(?P<value_column>.+?) lớn nhất\?"
        ),
    },
    "count": {
        "count_rows": re.compile(
            r"Có bao nhiêu dòng trong bảng (?P<table>\d+) "
            r"ở trang (?P<page>\d+) có "
            r"(?P<condition_column>.+?) là “(?P<condition_value>[^”]+)”\?"
        ),
    },
    # ... Danh sách mẫu câu đầy đủ được đính kèm ở Phụ lục
}
```

Các nhóm đặt tên như `table`, `page` và `value_column` giúp kết quả regex được chuyển thẳng vào `fields` của intent. Những mẫu cụ thể như Cross-page Sum và Visual Bold Lookup được thử trước mẫu chung để tránh chọn nhầm solver Lookup hoặc Sum.

#### Trích xuất điều kiện từ câu hỏi

Các giá trị dùng để xác định hàng thường nằm trong dấu ngoặc kép. Hàm dưới đây ghép mỗi giá trị với phần text đứng trước nó để tạo thành một cặp điều kiện.

```python
def parse_condition_pairs(text):
    matches = list(re.finditer(r"“([^”]+)”", text))
    pairs = []
    previous_end = 0

    for match in matches:
        column = text[previous_end:match.start()].strip()
        column = re.sub(r"^(?:và|với)\s+", "", column)
        column = re.sub(r"^(?:dòng(?:\s+có)?|đối\s+với)\s+", "", column)
        pairs.append((column.strip(" ,:.;"), match.group(1)))
        previous_end = match.end()

    return pairs
```

Chẳng hạn, đoạn `Phòng ban “Kế toán” và Định biên “30”` được chuyển thành:

```python
[("Phòng ban", "Kế toán"), ("Định biên", "30")]
```

Nếu câu hỏi một trang không khớp hoàn toàn với mẫu, hệ thống có thể nhận diện loại suy luận qua các dấu hiệu như `lớn nhất` hoặc `có bao nhiêu dòng`, rồi lấy từng thông tin cần thiết một cách độc lập. Hai dạng phức tạp hơn là Cross-page Sum và Visual Bold Lookup vẫn cần khớp mẫu chuyên biệt để tránh diễn giải sai cấu trúc câu hỏi. Intent chỉ được chuyển cho solver khi có đủ các trường được liệt kê trong `REQUIRED_FIELDS`.

```python
def parse_intent(question):
    matched = strong_template_match(question)
    if matched:
        reasoning_type, template, raw_fields = matched
        fields = normalize_fields(reasoning_type, raw_fields)
        return StructuredIntent(reasoning_type, template, fields, "strong_template")

    reasoning_type = heuristic_route(question)
    if reasoning_type is None:
        return StructuredIntent("unmatched", None, {}, "none")

    raw_fields = parse_fields_by_type(question, reasoning_type)
    fields = normalize_fields(reasoning_type, raw_fields)
    return StructuredIntent(reasoning_type, None, fields, "heuristic")

# ... Các hàm hỗ trợ đầy đủ được đính kèm ở Phụ lục
```

Kết quả của bước phân tích câu hỏi là một intent cho biết cần truy cập bảng nào, hàng nào, cột nào và thực hiện phép suy luận gì.

### Xác định vùng bảng và khôi phục cấu trúc không gian

Sau khi biết trang và số thứ tự bảng, hệ thống cần thu hẹp phạm vi OCR trước khi tìm hàng. Nếu tìm trên toàn bộ trang, những block có text giống nhau ở hai bảng khác nhau có thể bị ghép nhầm.

#### Khoanh vùng bảng

Tiêu đề bảng thường chứa từ `BẢNG` và có chiều rộng lớn. Hệ thống sắp xếp các tiêu đề theo trục Y, sau đó lấy những OCR block nằm giữa tiêu đề của bảng hiện tại và bảng kế tiếp.

```python
def table_blocks(layout, page, table_index):
    blocks = page_blocks(layout, page)
    titles = sorted(
        [
            block for block in blocks
            if block_width(block) >= 0.65
            and "BẢNG" in str(block["text"]).upper()
        ],
        key=lambda block: block["bbox"][1],
    )

    if not titles:
        return blocks if table_index == 1 else []

    start = titles[table_index - 1]["bbox"][1]
    end = titles[table_index]["bbox"][1] if table_index < len(titles) else 1.0
    return [block for block in blocks if start <= center(block)[1] < end]
```

Ngưỡng `0.65` là một quy tắc kinh nghiệm rút ra từ dataset: block tiêu đề chiếm ít nhất 65% chiều rộng trang. Đây không phải một mô hình có thể phát hiện mọi dạng bảng. Kết quả của hàm chỉ còn các OCR block thuộc bảng cần xử lý.

#### Khôi phục cấu trúc hàng và cột

OCR không cung cấp trực tiếp chỉ số hàng và cột. Hệ thống trước tiên nhóm các block có cùng vị trí mép trên `y1` để xác định các hàng vật lý, sau đó sắp xếp block trong mỗi hàng từ trái sang phải.

```python
def group_rows(blocks):
    grouped = {}
    for block in blocks:
        row_y = round(float(block["bbox"][1]), 6)
        grouped.setdefault(row_y, []).append(block)

    return [
        sorted(row, key=lambda block: center(block)[0])
        for _, row in sorted(grouped.items())
    ]
```

Một block đôi khi bao phủ nhiều hàng vật lý, thường xuất hiện ở các ô được gộp theo chiều dọc. Vì vậy, mỗi hàng vật lý tiếp tục được biểu diễn bằng một điểm `row_y` nằm giữa hai đường biên của hàng. Tất cả block có bounding box bao phủ điểm này được ghép thành một **hàng logic** hoàn chỉnh.

```python
def logical_row_at(blocks, physical_row):
    row_top = min(block["bbox"][1] for block in physical_row)
    row_bottom = min(
        block["bbox"][3]
        for block in physical_row
        if block["bbox"][3] > row_top
    )
    row_y = (row_top + row_bottom) / 2

    return [
        block for block in blocks
        if block["bbox"][1] <= row_y <= block["bbox"][3]
    ]
```

Nhờ bước này, một ô chung kéo dài qua nhiều dòng có thể xuất hiện trong từng hàng logic mà nó đại diện. Cách biểu diễn hàng logic được dùng khi solver cần duyệt hoặc so sánh toàn bộ các hàng. Với truy xuất đơn giản, hàng vật lý thường đã đủ để tìm đúng cell.

Với cột, tâm theo trục X của header được dùng làm mốc. Cell có vùng ngang bao quanh tâm header được xem là cell thuộc cột đó.

```python
def cell_under(row, header):
    header_x, _ = center(header)
    candidates = [
        cell for cell in row
        if cell["bbox"][0] <= header_x <= cell["bbox"][2]
    ]

    if candidates:
        return min(candidates, key=lambda cell: abs(center(cell)[0] - header_x))
    return min(row, key=lambda cell: abs(center(cell)[0] - header_x)) if row else None
```

Việc chọn cell gần tâm nhất giúp xử lý trường hợp một hàng có nhiều block cùng bao quanh vị trí header. Nếu không có block nào bao quanh tâm, hệ thống dùng cell gần nhất làm phương án dự phòng. Sau bước này, hệ thống có thể truy cập một cell thông qua hàng dữ liệu và tên cột thay vì chỉ làm việc với danh sách OCR block rời rạc.

### Truy xuất hàng và ô đích

Input của bước truy xuất gồm các block trong bảng và `condition_pairs` lấy từ intent. Mục tiêu là tìm đúng hàng thỏa tất cả điều kiện rồi lấy **ô đích**, tức ô nằm trong cột được câu hỏi yêu cầu.

```python
def matching_rows(blocks, pairs):
    headers = [header_block(blocks, column) for column, _ in pairs]
    if not pairs or any(header is None for header in headers):
        return []

    matches = []
    for row in data_rows(blocks, headers):
        cells = [cell_under(row, header) for header in headers]
        if all(
            cell is not None and str(cell["text"]) == value
            for cell, (_, value) in zip(cells, pairs)
        ):
            matches.append((row, cells))

    return matches
```

Ví dụ, với hai điều kiện `Phòng ban = Kế toán` và `Định biên = 30`, mỗi hàng được chiếu lên hai cột tương ứng rồi so khớp text. Một hàng chỉ được giữ lại khi thỏa đồng thời cả hai điều kiện.

```python
def resolve_target_cell(layout, *, page, table, target_column, condition_pairs):
    blocks = table_blocks(layout, page, table)
    matches = matching_rows(blocks, condition_pairs)
    target_header = header_block(blocks, target_column)

    if len(matches) != 1 or target_header is None:
        return None

    row, condition_cells = matches[0]
    answer_cell = cell_under(row, target_header)
    return answer_cell, condition_cells + [answer_cell]
```

Hàm chỉ trả kết quả khi tìm được đúng một hàng, qua đó tránh chọn tùy ý khi điều kiện còn mơ hồ. Kết quả gồm ô đích và các block đã dùng để xác định nó. Các block này đồng thời là cơ sở để tạo evidence.

Evidence được tạo trực tiếp từ các OCR block đã tham gia truy xuất. Hàm dưới đây loại bỏ block trùng nhau và chỉ giữ hai trường mà định dạng submission yêu cầu.

```python
def build_evidence(blocks):
    evidence, seen = [], set()

    for block in blocks:
        item = (int(block["page"]), tuple(block["bbox"]))
        if item in seen:
            continue

        seen.add(item)
        evidence.append({"page": item[0], "bbox": list(item[1])})

    return evidence
```

Việc giữ lại chính các ô điều kiện và ô đích trong suốt pipeline giúp answer và evidence dùng chung một nguồn dữ liệu, thay vì tìm evidence lại bằng một bước độc lập dễ gây lệch kết quả.

### Thực hiện suy luận trên dữ liệu đã truy xuất

Các solver sử dụng chung kết quả truy xuất nhưng khác nhau ở phép toán cuối cùng. Tất cả đều trả về cùng một dạng `(answer, evidence)`, vì vậy bước điều phối không cần biết cách từng solver xử lý bên trong.

#### Tra cứu trực tiếp (Lookup)

Lookup là trường hợp trực tiếp nhất: tìm một hàng rồi đọc text tại giao điểm giữa hàng đó và target column.

```python
def solve_lookup(fields, layout):
    resolved = resolve_target_cell(layout, **fields)
    if resolved is None:
        return None

    answer_cell, evidence = resolved
    return str(answer_cell["text"]), build_evidence(evidence)
```

Answer giữ nguyên text OCR, còn evidence gồm các ô điều kiện và ô đáp án. Cặp `(answer, evidence)` này cũng là định dạng đầu ra chung của các solver còn lại.

#### Đếm và tính tổng (Count và Sum)

Count giữ tất cả các hàng thỏa điều kiện và trả về số lượng hàng. Evidence chỉ gồm những ô điều kiện chứng minh các hàng đã được đếm.

```python
def solve_count(fields, layout):
    table, page = fields["table"], fields["page"]
    blocks = table_blocks(layout, page, table)
    matches = matching_rows(blocks, fields["condition_pairs"])
    evidence = [cell for _, cells in matches for cell in cells]
    return str(len(matches)), build_evidence(evidence)
```

Sum tách chuỗi điều kiện thành hai nhóm, tìm một hàng cho mỗi nhóm rồi lấy hai ô trong cùng cột đích. Nội dung chữ trong ô được chuyển thành số trước khi cộng.

```python
def solve_sum(fields, layout):
    blocks = table_blocks(layout, fields["page"], fields["table"])
    first_row, second_row = split_two_conditions(
        blocks, fields["condition_pairs"]
    )
    target_header = header_block(blocks, fields["target_column"])

    first_cell = cell_under(first_row[0], target_header)
    second_cell = cell_under(second_row[0], target_header)
    answer = parse_number(first_cell["text"]) + parse_number(second_cell["text"])

    evidence = first_row[1] + second_row[1] + [first_cell, second_cell]
    return format_number(answer), build_evidence(evidence)

# ... Phần xử lý đầy đủ được đính kèm ở Phụ lục
```

`parse_number()` xử lý cách viết số có dấu chấm, dấu phẩy hoặc ký hiệu phần trăm, còn `format_number()` đưa kết quả về định dạng chuỗi dùng trong submission. Evidence được giữ từ các OCR block gốc thay vì tạo từ giá trị số đã chuyển đổi.

#### So sánh hai hàng (Compare)

Compare nhận hai nhóm điều kiện, truy xuất hai hàng và lấy ô chứa giá trị cần so sánh của mỗi hàng. Đối tượng thuộc hàng có giá trị cao hơn được dùng làm answer.

```python
first, second = matched[0][0], matched[1][0]
first_value_cell = cell_under(first[0], value_header)
second_value_cell = cell_under(second[0], value_header)

first_value = parse_number(first_value_cell["text"])
second_value = parse_number(second_value_cell["text"])
winner = first if first_value > second_value else second

answer_cell = winner[1][0]
evidence = first[1] + second[1] + [first_value_cell, second_value_cell]
return str(answer_cell["text"]), build_evidence(evidence)
```

Mặc dù answer chỉ thuộc một hàng, evidence vẫn chứa điều kiện và giá trị của cả hai hàng vì cả hai đều tham gia phép so sánh.

#### Tìm giá trị cực trị (Argmax và Argmin)

Argmax và Argmin sử dụng các hàng logic đã được khôi phục ở bước trước, chuyển ô thuộc cột cần xếp hạng của từng hàng thành số rồi dùng `max()` hoặc `min()` để chọn hàng có giá trị lớn nhất hoặc nhỏ nhất. Để tạo evidence, hệ thống lấy các ô định danh của hàng được chọn theo thứ tự từ trái sang phải và dừng ngay khi tập ô đã chọn đủ để phân biệt hàng này với các hàng còn lại. Cuối cùng, ô chứa giá trị cực trị được bổ sung vào evidence.

```python
_, return_cell, value_cell, winner_row = select(
    candidates, key=lambda item: item[0]
)

value_x, _ = center(value_header)
candidate_rows = [row for _, _, _, row in candidates]
row_prefixes = [
    [cell for cell in row if center(cell)[0] < value_x]
    for row in candidate_rows
]
identifier_cells = [cell for cell in winner_row if center(cell)[0] < value_x]

for size in range(1, len(identifier_cells) + 1):
    texts = [cell["text"] for cell in identifier_cells[:size]]
    same_rows = [
        prefix for prefix in row_prefixes
        if [cell["text"] for cell in prefix[:size]] == texts
    ]
    if len(same_rows) == 1:
        identifier_cells = identifier_cells[:size]
        break

return str(return_cell["text"]), build_evidence(identifier_cells + [value_cell])
```

Chẳng hạn, nếu ô đầu tiên `Kế toán` đã xác định duy nhất hàng thắng thì evidence không cần thêm ô định danh khác. Nếu bảng có hai hàng cùng mang tên `Kế toán`, hệ thống tiếp tục lấy ô kế bên, chẳng hạn `Định biên = 30`, để phân biệt. Khi đó evidence gồm `Kế toán`, `30` và ô giá trị cực trị. Cơ chế này cung cấp đủ bằng chứng nhưng tránh đưa toàn bộ hàng vào submission.

### Tính tổng giữa nhiều trang (Cross-page Sum)

Cross-page Sum không cần một cơ chế truy xuất mới. Mỗi **toán hạng**, tức mỗi số cần cộng, được mô tả bằng trang, bảng, cột đích và các điều kiện xác định hàng riêng, sau đó được xử lý lại bằng `resolve_target_cell()`.

```python
def solve_cross_page_sum(fields, layout):
    operands = fields["operands"]
    resolved = [
        resolve_target_cell(layout, **operand)
        for operand in operands
    ]

    cells = [item[0] for item in resolved]
    values = [parse_number(cell["text"]) for cell in cells]
    evidence = [block for _, blocks in resolved for block in blocks]

    return format_number(sum(values)), build_evidence(evidence)
```

Các block vẫn giữ số trang gốc nên evidence có thể chứa bbox từ cả trang 1 và trang 2. Kết quả của nhánh này vẫn có cùng dạng với Sum thông thường, nhờ đó không cần thay đổi phần điều phối phía sau.

### Nhận diện hàng in đậm từ ảnh (Visual Bold Lookup)

Visual Bold Lookup là nhánh duy nhất cần sử dụng ảnh gốc. Tuy nhiên, hệ thống không phân tích toàn bộ trang bằng mô hình thị giác. Nội dung OCR và vị trí trước tiên được dùng để thu hẹp phạm vi xuống đúng hai hàng ứng viên. Ảnh chỉ được dùng để quyết định hàng nào in đậm hơn.

#### Ước lượng độ rộng nét chữ

**Độ rộng nét (stroke width)** mô tả độ dày trung bình của các nét tạo nên ký tự. Với mỗi cell, hệ thống cắt vùng ảnh theo bbox. Otsu thresholding tự chọn một ngưỡng sáng tối để tách nét chữ khỏi nền giấy. Sau đó, distance transform đo khoảng cách từ mỗi điểm bên trong nét chữ tới biên gần nhất. Khoảng cách trung bình nhân đôi được dùng để ước lượng độ dày của nét.

```python
def cell_stroke_width(cell, image):
    height, width = image.shape
    x1, y1, x2, y2 = cell["bbox"]
    crop = image[
        int(y1 * height):int(y2 * height),
        int(x1 * width):int(x2 * width),
    ]
    _, ink = cv2.threshold(
        crop, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    distance = cv2.distanceTransform(ink, cv2.DIST_L2, 3)
    return float(2 * distance[ink > 0].mean())


def row_boldness_score(row, image):
    scores = [cell_stroke_width(cell, image) for cell in row]
    return float(np.median([score for score in scores if score is not None]))

# ... Phần xử lý ảnh đầy đủ được đính kèm ở Phụ lục
```

**Trung vị (median)** được dùng thay cho trung bình để một cell bị nhiễu hoặc có đường viền dày bất thường không làm lệch điểm của cả hàng. Nếu chênh lệch điểm giữa hai hàng lớn hơn `VISUAL_SCORE_MARGIN = 0.02`, hàng có điểm cao hơn được chọn. Khi hai điểm quá gần nhau, hệ thống so sánh các cell ở cùng vị trí của hai hàng. Mỗi cặp bỏ một phiếu cho cell có nét dày hơn, rồi hàng nhận nhiều phiếu hơn được chọn.

#### Huấn luyện ResNet18 để so sánh từng cặp hàng

Nếu cả điểm trung vị và việc bỏ phiếu theo cell đều chưa cho kết quả rõ ràng, hai hàng được cắt khỏi ảnh và đưa vào **ResNet18**, một mạng nơ-ron dùng để trích xuất đặc trưng hình ảnh. Mạng biến mỗi hàng thành một dãy số mô tả đặc điểm thị giác, sau đó ghép hai dãy số để dự đoán hàng thứ nhất hay hàng thứ hai in đậm hơn.

Notebook `train_bold_pair_colab.ipynb` tạo các cặp hàng từ Training set và chia dữ liệu theo document để cùng một tài liệu không xuất hiện ở cả tập huấn luyện lẫn tập validation. Mô hình sau khi huấn luyện được lưu vào checkpoint `bold_pair_resnet18.pt`.

```python
class BoldPairResNet18(nn.Module):
    def __init__(self):
        super().__init__()
        backbone = resnet18(weights=None)
        self.encoder = nn.Sequential(*list(backbone.children())[:-1])
        self.head = nn.Linear(1024, 2)

    def forward(self, first, second):
        first_features = self.encoder(first).flatten(1)
        second_features = self.encoder(second).flatten(1)
        return self.head(torch.cat([first_features, second_features], dim=1))


model = BoldPairResNet18().to(DEVICE)
checkpoint = torch.load(CHECKPOINT_PATH, map_location=DEVICE, weights_only=True)
model.load_state_dict(checkpoint["state_dict"])
model.eval()
```

Trong notebook huấn luyện, **encoder** là phần ResNet18 biến ảnh thành đặc trưng. Encoder được khởi tạo từ bộ trọng số đã học trên ImageNet, nhờ đó mô hình không phải học đặc trưng hình ảnh từ đầu. Khi dự đoán, `weights=None` được dùng lúc tạo kiến trúc vì toàn bộ trọng số sẽ được nạp lại từ checkpoint. Hệ thống chỉ dùng kết quả khi mô hình gán cho hàng thắng xác suất từ `0.60` trở lên. Nếu thấp hơn, hai hàng được xem là chưa thể phân biệt đủ chắc chắn.

#### Kết hợp các tầng quyết định

Ba mức được thực hiện từ đơn giản đến phức tạp: so sánh trung vị độ rộng nét của cả hàng, bỏ phiếu giữa các cặp cell, rồi mới dùng ResNet18.

```python
candidate_rows = retrieve_candidate_rows(fields, layout)
row_scores = score_rows(candidate_rows, image)
cell_scores = score_corresponding_cells(candidate_rows, image)

winner = choose_bolder_row(row_scores)
if winner is None:
    winner = choose_bolder_vote(*cell_scores)
if winner is None:
    winner = pairwise_bold_winner(layout, page, candidate_rows)
if winner is None:
    return None
```

Sau khi có hàng thắng, answer được đọc tại cột đích. Evidence gồm các ô điều kiện của cả hai hàng ứng viên và ô đáp án của hàng in đậm, vì cả hai ứng viên đều được dùng trong quá trình so sánh.

### Điều phối các nhánh suy luận

Mỗi loại suy luận được nối với một solver tương ứng trong `SOLVERS`. Vì tất cả solver đều nhận `fields` cùng `DocumentLayout` và trả về `(answer, evidence)`, vòng lặp dự đoán có thể gọi chúng theo cùng một cách.

```python
SOLVERS = {
    "lookup": solve_lookup,
    "count": solve_count,
    "sum": solve_sum,
    "argmax": solve_argmax,
    "argmin": solve_argmin,
    "compare": solve_compare,
    "cross_page_sum": solve_cross_page_sum,
    "visual_bold_lookup": solve_visual_bold_lookup,
}


def solve(intent, layout):
    solver = SOLVERS.get(intent.reasoning_type)
    if solver is None or not intent_is_complete(intent):
        return None
    return solver(intent.fields, layout)
```

Pipeline duyệt từng câu hỏi theo quy trình đã xây dựng: tạo intent, lấy `DocumentLayout`, gọi solver rồi ghi `question_id`, `answer` và `evidence` thành một dòng JSON. Nếu intent chưa đủ thông tin hoặc không truy xuất được dữ liệu, hệ thống trả về `không xác định` cùng evidence rỗng thay vì tự đoán. Cuối cùng, notebook đóng gói `predictions.jsonl` vào file ZIP theo định dạng của cuộc thi. Phần code hoàn chỉnh được đính kèm ở Phụ lục.

### Kết quả đánh giá

Sau khi chạy toàn bộ các cell trong notebook trên Training set, pipeline đạt kết quả như sau:

| Loại suy luận | ANLS | Evidence-F1 | Điểm tổng hợp |
|---|---:|---:|---:|
| Lookup | 100,00% | 100,00% | 100,00% |
| Count | 100,00% | 100,00% | 100,00% |
| Sum | 100,00% | 100,00% | 100,00% |
| Argmax | 90,02% | 77,52% | 88,14% |
| Argmin | 89,00% | 76,49% | 87,12% |
| Compare | 100,00% | 100,00% | 100,00% |
| Cross-page Sum | 100,00% | 100,00% | 100,00% |
| Visual Bold Lookup | 96,90% | 74,82% | 93,59% |
| **Toàn bộ Training set** | **96,25%** | **90,89%** | **95,45%** |

---

# Phụ lục

1. **Dữ liệu:** Tải [`data.zip`](https://drive.google.com/file/d/1puQYjYL_hgd_zNTZgbjlPplcKUYGHOjo/view?usp=sharing) và giải nén vào `DocViVQA/data/`.
2. **Code hoàn chỉnh:** Repository của tutorial được cung cấp [tại đây](https://github.com/T-Sunm/olp-ai-ptit-2026-preliminary-round), bao gồm các notebook [`explore_dataset.ipynb`](notebooks/explore_dataset.ipynb), [`train_bold_pair_colab.ipynb`](notebooks/train_bold_pair_colab.ipynb), [`submission_pipeline.ipynb`](notebooks/submission_pipeline.ipynb) và script [`evaluate_predictions.py`](scripts/evaluate_predictions.py) dùng để chấm prediction trên Training set.

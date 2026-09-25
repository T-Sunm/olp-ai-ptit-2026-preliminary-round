# 4. Image Processing & Table Detection

## 4.1 Document Deskew

| Slide Title Mục tiêu chính  |                                        |                                                                                                                                                                                                                       |
| --------------------------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**                       | **Why Deskew?**                        | Cho thấy skew làm directional line extraction, projection và cell cropping kém ổn định. Dùng ví dụ 0°, 2°, 5°. Ghi rõ 5° chỉ để minh họa tác hại, không phải guaranteed range của implementation hiện tại.            |
| **2**                       | **From Intensity Change to Edge**      | Giải thích trực giác edge xuất hiện nơi độ sáng thay đổi nhanh. Dùng intensity profile và đạo hàm để tạo cầu nối sang Sobel.                                                                                          |
| **3**                       | **Sobel: Detecting Change in X and Y** | Giới thiệu `Gx`, `Gy`, hai Sobel kernels và trực giác vì sao Sobel X làm nổi vertical edges, Sobel Y làm nổi horizontal edges.                                                                                        |
| **4**                       | **Gradient Magnitude & Direction**     | Từ `Gx`, `Gy` tạo gradient magnitude và direction. Nhấn mạnh gradient direction thường vuông góc với edge.                                                                                                            |
| **5**                       | **Canny Edge Detection: Overview**     | Trình bày flow tổng quát: Gaussian smoothing → gradient → NMS → double threshold → hysteresis. Canny tạo edge map sạch và mảnh hơn, đồng thời cố gắng giữ các edge có liên kết.                                       |
| **6**                       | **Why NMS & Hysteresis?**              | Giải thích hai bước quan trọng nhất của Canny: NMS làm mảnh edge, hysteresis giữ weak edges khi chúng nối với strong edges. Không nói Canny đảm bảo nối mọi edge bị đứt.                                              |
| **7**                       | **From Edge Pixels to Straight Lines** | Tạo transition từ Canny sang Hough: Canny cho edge pixels, Hough tìm những edge pixels cùng thuộc một line.                                                                                                           |
| **8**                       | **Hough Space, Voting & Peaks**        | Giới thiệu `(ρ, θ)`, point → sinusoid, nhiều collinear points → accumulator peak. Nhấn mạnh `θ` là hướng của normal line.                                                                                             |
| **9**                       | **HoughLinesP for Deskew**             | Giải thích tại sao implementation chọn `HoughLinesP`: trả line segments với hai endpoints nên thuận tiện để tính angle, lọc theo length và visualize. Nhấn mạnh `HoughLines` vẫn có thể dùng để estimate orientation. |
| **10**                      | **Estimate Skew & Rotate**             | Flow cuối: Canny → Hough segments → giữ near-horizontal lines → lấy median angle → rotate image. Gộp failure modes và checkpoint ở cuối slide.                                                                        |

## Why Deskew?

Một bảng trong ảnh thường có các hàng chạy ngang và các cột chạy dọc. Khi ảnh nằm thẳng, những đường này cũng gần song song với cạnh ảnh, nên các bước xử lý phía sau dễ xác định vị trí hàng, cột và từng ô. Khi ảnh bị nghiêng, cùng một đường ngang sẽ không còn nằm ở một độ cao cố định nữa. Nó đi chéo qua nhiều vị trí khác nhau trên ảnh. Vì vậy, những bước dùng để tìm hàng hoặc cột sẽ khó nhận ra một đường rõ ràng như trước.

Ví dụ, với một đường ngang nằm thẳng, các pixel của nó tập trung gần cùng một vị trí theo chiều dọc. Nhưng nếu đường đó bị nghiêng, các pixel bị trải ra trên nhiều vị trí. Kết quả là ranh giới giữa các hàng và cột trở nên khó xác định chính xác hơn.

Điều này tiếp tục ảnh hưởng tới bước cắt từng ô. Nếu vị trí hàng và cột không ổn định, vùng cắt có thể lệch, lấy thiếu nội dung hoặc ăn sang ô bên cạnh.

**[CHÈN HÌNH: cùng một bảng ở 0°, 2° và 5°]**

*Hình. Khi bảng bị nghiêng, các đường vốn nằm ngang hoặc dọc bắt đầu lệch khỏi trục của ảnh, khiến việc xác định hàng, cột và vùng ô kém ổn định hơn.*

Vì vậy, mục tiêu của deskew là:

> **Tìm xem trang đang nghiêng bao nhiêu và xoay nó trở lại gần trạng thái thẳng trước khi phục hồi cấu trúc bảng.**

Trong dữ liệu M1/M2 đã quan sát, phần lớn trang vốn đã khá thẳng. Vì vậy deskew ở đây nên được xem là một bước tăng độ ổn định cho các trường hợp bị lệch, không phải một yêu cầu bắt buộc do EDA đặt ra.

## From Intensity Change to Edge

Trước khi đi vào Sobel, ta cần hiểu một ý tưởng cơ bản của edge detection: **edge thường xuất hiện ở nơi độ sáng thay đổi nhanh**.

Hãy tưởng tượng ta lấy một đường quét đi ngang qua ảnh. Khi di chuyển dọc theo đường này, mỗi vị trí sẽ có một mức sáng khác nhau.

Ta ký hiệu:

- `t` là **vị trí hiện tại trên đường quét**
- `f(t)` là **độ sáng của ảnh tại vị trí `t`**

Nói cách khác, `f(t)` trả lời câu hỏi:

> "Tại vị trí này trên ảnh, pixel sáng bao nhiêu?"

**[CHÈN HÌNH: Image region → Intensity profile → Rate of change]**

*Hình. Khi đường quét đi qua một ranh giới trong ảnh, intensity thay đổi nhanh và tạo ra một peak trong rate of change.*

Ở biểu đồ giữa, `f(t)` mô tả cách intensity thay đổi khi ta di chuyển dọc theo đường quét.

Trong một vùng tương đối đồng đều, các pixel lân cận có độ sáng gần giống nhau nên `f(t)` thay đổi chậm. Khi đi qua ranh giới giữa hai vùng sáng tối khác nhau, `f(t)` thay đổi nhanh hơn rõ rệt.

Tuy nhiên, chỉ biết `f(t)` vẫn chưa trực tiếp cho ta biết vị trí nào thay đổi mạnh nhất. Vì vậy ta xét:

`f'(t)`

Trong đó `f'(t)` là **đạo hàm của `f(t)`**, tức đại lượng đo xem intensity đang thay đổi nhanh đến mức nào tại vị trí `t`.

Có thể hiểu đơn giản:

- `f(t)` trả lời: **"Độ sáng hiện tại là bao nhiêu?"**
- `f'(t)` trả lời: **"Độ sáng đang thay đổi nhanh đến mức nào?"**

Ở những vùng đồng đều, intensity gần như không đổi nên `f'(t)` nhỏ.

Tại vùng chuyển tiếp giữa tối và sáng, intensity thay đổi nhanh nhất nên `f'(t)` tạo ra một peak. Vị trí của peak này chính là một ứng viên mạnh cho edge.

Điểm quan trọng là **pixel sáng không đồng nghĩa với edge**. Một vùng trắng hoàn toàn có thể có `f(t)` rất lớn nhưng `f'(t)` gần bằng 0 vì độ sáng hầu như không thay đổi giữa các pixel lân cận.

Ví dụ này mới chỉ xét sự thay đổi theo **một hướng**. Nhưng ảnh thực tế là 2D, nên từ một pixel, intensity có thể thay đổi theo cả:

- trái ↔ phải
- trên ↕ dưới

Vì vậy, bước tiếp theo là đo mức thay đổi intensity theo **hai hướng X và Y**. Đây chính là ý tưởng dẫn đến **Sobel Edge Detection**.

## Sobel: Detecting Change in X and Y

Ở ví dụ trước, ta mới chỉ xét intensity thay đổi dọc theo một đường quét. Nhưng ảnh thực tế là 2D, nên tại cùng một pixel, độ sáng có thể thay đổi theo cả hướng trái ↔ phải và trên ↕ dưới. Vì vậy, thay vì chỉ cần một giá trị giống đạo hàm 1D, ta cần đo mức thay đổi theo hai hướng. Đây chính là ý tưởng của Sobel.

Sobel sử dụng hai kernel nhỏ để ước lượng mức thay đổi intensity theo trục X và trục Y. Kết quả theo trục X được ký hiệu là $G_x$, còn theo trục Y là $G_y$.

Có thể hiểu đơn giản:

- $G_x$ trả lời câu hỏi: **“độ sáng thay đổi mạnh đến đâu khi đi từ trái sang phải?”**
- $G_y$ trả lời câu hỏi: **“độ sáng thay đổi mạnh đến đâu khi đi từ trên xuống dưới?”**

Hai kernel Sobel thường dùng là:

$$

G_x =

\begin{bmatrix}

-1 & 0 & 1\\\\

-2 & 0 & 2\\\\

-1 & 0 & 1

\end{bmatrix}

\qquad

G_y =

\begin{bmatrix}

1 & 2 & 1\\\\

0 & 0 & 0\\\\

-1 & -2 & -1

\end{bmatrix}

$$

Không cần nhớ ngay từng con số. Điều quan trọng là cách các trọng số được sắp xếp.

Kernel $G_x$ gần giống việc so sánh vùng bên trái với vùng bên phải. Nếu hai phía có độ sáng gần giống nhau, response sẽ nhỏ. Nếu một phía tối còn phía kia sáng rõ rệt, response sẽ lớn.

$G_y$ làm điều tương tự nhưng so sánh vùng phía trên với vùng phía dưới.

**[CHÈN HÌNH: ảnh gốc → Sobel X → Sobel Y]**

*Hình. Sobel X làm nổi các thay đổi theo trái ↔ phải, còn Sobel Y làm nổi các thay đổi theo trên ↕ dưới.*

Có một điểm rất dễ gây nhầm. $G_x$ đo thay đổi theo hướng trái ↔ phải, nhưng lại thường làm nổi bật **vertical edges**.

Lý do là để phát hiện một cạnh dọc, ta phải đi cắt ngang cạnh đó theo hướng trái → phải. Khi đi qua cạnh, intensity thay đổi mạnh nên $G_x$ có response lớn.

Tương tự, $G_y$ đo thay đổi theo hướng trên ↕ dưới nên thường làm nổi bật **horizontal edges**, vì ta phát hiện cạnh ngang bằng cách đi cắt qua nó theo hướng trên → dưới.

Một chi tiết nhỏ nhưng khá trực quan xuất hiện khi áp dụng Sobel lên các đường kẻ dày của bảng. Ở ảnh gốc, một đường kẻ đen có thể rộng vài pixel. Sobel không làm sáng toàn bộ đường kẻ đó, mà chủ yếu phản ứng ở **hai mép** của đường.

Lý do là bên trong phần ruột của đường kẻ, các pixel đều có độ sáng gần giống nhau. Nếu hình dung lại theo ý tưởng đạo hàm ở slide trước, intensity trong vùng này gần như không đổi nên:

$$

f'(t) \approx 0

$$

Vì response gần 0 nên phần giữa của đường kẻ xuất hiện tối trên Sobel result.

Ngược lại, ở hai mép của đường kẻ:

$$

\text{trắng} \rightarrow \text{đen}

$$

và

$$

\text{đen} \rightarrow \text{trắng}

$$

intensity thay đổi mạnh, nên Sobel tạo ra hai vùng response lớn tương ứng với hai biên của cùng một đường kẻ.

## Gradient Magnitude & Direction

Sau Sobel, tại mỗi pixel ta có hai giá trị là $G_x$ và $G_y$. Có thể xem chúng như hai thành phần của cùng một sự thay đổi intensity: $G_x$ cho biết mức thay đổi theo trái ↔ phải, còn $G_y$ cho biết mức thay đổi theo trên ↕ dưới.

Từ hai thành phần này, ta tạo thành một vector gradient:

$$

\mathbf{G} = (G_x, G_y)

$$

Vector này cho ta hai thông tin quan trọng.

Đầu tiên là **gradient magnitude**, tức độ mạnh của sự thay đổi:

$$

G = \sqrt{G_x^2 + G_y^2}

$$

Có thể hiểu đơn giản, magnitude trả lời câu hỏi:

> "Tại pixel này, intensity đang thay đổi mạnh đến mức nào?"

Nếu $G$ nhỏ, vùng ảnh tương đối đồng đều. Nếu $G$ lớn, pixel nằm ở nơi intensity thay đổi mạnh và vì vậy là một ứng viên edge đáng chú ý.

Thông tin thứ hai là **gradient direction**, thường được tính bằng:

$$

\theta = \operatorname{atan2}(G_y, G_x)

$$

Direction trả lời câu hỏi:

> "Intensity đang thay đổi mạnh nhất theo hướng nào?"

Nếu $G_x$ lớn hơn nhiều so với $G_y$, gradient gần nằm ngang. Nếu $G_y$ lớn hơn, gradient gần thẳng đứng. Nếu cả hai đều đáng kể, gradient sẽ nghiêng theo một hướng chéo.

**[CHÈN HÌNH: Gx + Gy → gradient vector → magnitude & direction]**

*Hình. $G_x$ và $G_y$ kết hợp thành gradient vector, từ đó suy ra độ mạnh và hướng của sự thay đổi intensity.*

Điểm quan trọng nhất là **gradient direction thường không chạy dọc theo edge**. Nó thường chỉ theo hướng cắt ngang edge, vì đó là hướng mà intensity thay đổi nhanh nhất.

Ví dụ, nếu có một vertical edge ngăn cách vùng tối bên trái và vùng sáng bên phải, khi ta đi dọc theo edge thì intensity gần như không đổi. Nhưng khi đi từ trái sang phải, tức cắt ngang edge, intensity thay đổi rất mạnh.

Vì vậy gradient sẽ hướng từ vùng tối sang vùng sáng và gần **vuông góc** với vertical edge.

Tương tự, với horizontal edge, gradient thường hướng theo phương trên ↕ dưới.

Do đó có thể nhớ:

> **Gradient direction thường vuông góc với edge direction.**

Đây là insight rất quan trọng vì ở bước Canny tiếp theo, hướng gradient sẽ được dùng để xác định nên so sánh pixel với những điểm nào khi làm mảnh edge.

## Canny Edge Detection: Overview

Sau Sobel, ta đã biết ở đâu intensity thay đổi mạnh. Nhưng nếu nhìn panel **Gradient magnitude**, ta thấy kết quả vẫn chưa thể dùng trực tiếp làm edge map cuối cùng. Các đường kẻ của bảng và nét chữ đều sáng lên, nhiều đường còn khá dày, và những thay đổi nhỏ trong ảnh cũng có thể tạo ra các vệt sáng.

Canny xử lý dần những vấn đề đó qua năm bước.

**[CHÈN HÌNH: Gaussian smoothing → Gradient magnitude → NMS → Double threshold → Hysteresis]**

*Hình. Cùng một vùng bảng được theo dõi qua năm bước của Canny.*

### 1. Gaussian smoothing

Ở panel đầu tiên, ảnh vẫn là ảnh xám bình thường nhưng đã được làm mượt nhẹ. Chữ và đường kẻ vẫn còn nhìn thấy rõ, trong khi những thay đổi rất nhỏ giữa các pixel lân cận được giảm bớt.

Điều này quan trọng vì ở bước tiếp theo, mọi thay đổi sáng tối đều có thể tạo gradient. Nếu noise vẫn còn mạnh, nó cũng có thể bị hiểu nhầm thành edge.

Vì vậy kết quả của bước này chưa phải edge. Nó chỉ tạo ra một ảnh **ổn định hơn để đo sự thay đổi intensity**.

### 2. Gradient magnitude

Ở panel thứ hai, nền chuyển thành đen còn những nơi intensity thay đổi mạnh trở thành các vùng sáng.

Có thể nhìn trực tiếp vào hình:

- hai bên của các đường kẻ bảng sáng lên
- viền của các chữ và con số cũng sáng lên
- vùng trắng đồng đều bên trong cell gần như đen vì intensity ở đó ít thay đổi

Như vậy, pixel càng sáng ở panel này thì **mức thay đổi intensity tại pixel đó càng lớn**.

Tuy nhiên, hãy nhìn các đường kẻ của bảng. Chúng chưa xuất hiện thành một đường mảnh duy nhất mà thường thành **một dải sáng có bề rộng**. Điều đó có nghĩa là cùng một ranh giới đang được biểu diễn bởi nhiều pixel nằm cạnh nhau. Nếu dùng trực tiếp kết quả này làm edge map, ta sẽ khó xác định **chính xác edge nằm ở vị trí nào**, và một đường thật có thể bị hiểu thành nhiều đường gần nhau. Vì vậy, gradient magnitude mới chỉ cho biết **vùng nào có khả năng chứa edge**, chưa cho ta vị trí edge đủ gọn và chính xác.

### 3. Non-Maximum Suppression

Sang panel **NMS**, hãy so trực tiếp với panel Gradient magnitude. Các viền trắng quanh chữ và đường kẻ đã mảnh hơn.

Ví dụ một đường kẻ ngang ở panel trước có thể tạo ra vài hàng pixel cùng sáng. NMS nhìn theo hướng cắt ngang đường đó và chỉ giữ pixel có gradient lớn nhất, còn các pixel sáng nhưng yếu hơn ở hai bên bị đưa về 0.

Vì vậy:

- **trước NMS:** một boundary có thể là một dải sáng
- **sau NMS:** boundary được thu lại gần thành một đường mảnh

Kết quả này quan trọng vì bước Hough phía sau cần biết **edge nằm ở đâu**, chứ không cần một vùng rộng gồm nhiều pixel cùng mô tả một boundary.

### 4. Double Threshold

Sau NMS, các edge đã mảnh hơn nhưng vẫn có một vấn đề: **không phải pixel edge nào cũng đáng tin như nhau**.

Trong panel thứ tư của hình:

- **màu đỏ** là những pixel có gradient đủ lớn để được xem là **strong edge**
- **màu vàng** là những pixel yếu hơn, được xem là **weak edge**
- những pixel quá yếu không còn được hiển thị vì đã bị loại

Nhìn vào ảnh có thể thấy các đường kẻ rõ của bảng có nhiều đoạn màu đỏ. Trong khi đó, quanh chữ, số và một số đoạn đường kẻ yếu hơn có nhiều pixel màu vàng. Đây chính là ý nghĩa của “weak edge”. Nó không phải một khái niệm trừu tượng, mà là **những pixel màu vàng bạn đang thấy trong panel 4**. Gradient tại đó có tồn tại, nhưng chưa đủ mạnh để ta tin tưởng ngay.

Nếu chỉ dùng một threshold cao, rất nhiều đoạn vàng có thể bị mất dù chúng thật sự thuộc một edge. Nếu dùng threshold thấp, ta lại giữ quá nhiều pixel không đáng tin. Vì vậy Canny giữ tạm cả hai nhóm để bước cuối quyết định tiếp.

### 5. Hysteresis

Bây giờ hãy so panel **Double threshold** với panel **Hysteresis**. Ở panel 4 còn khá nhiều đoạn vàng, đặc biệt quanh chữ và các đoạn edge yếu. Sang panel 5, nhiều đoạn trong số đó biến mất.

Quy tắc là:

- pixel đỏ được giữ
- pixel vàng được giữ **nếu nó nối với một chuỗi edge dẫn tới pixel đỏ**
- pixel vàng đứng riêng, không nối với strong edge, bị loại

Ví dụ, nếu một phần đường **kẻ bảng hơi mờ nên chỉ hiện màu vàng** nhưng nó **nối liền với một đoạn đỏ của cùng đường kẻ**, nó vẫn được giữ. Ngược lại, một cụm vàng nhỏ nằm riêng quanh noise hoặc một chi tiết yếu không nối vào strong edge sẽ biến mất.

Vì vậy hysteresis không có nghĩa là **“nối mọi đoạn bị đứt lại”**. Nó chỉ dùng strong edges như các điểm đáng tin cậy để quyết định weak edges nào có lý do để tồn tại.

Sau bước này, panel cuối chỉ còn các edge pixels được giữ lại. Trong ví dụ của bạn, cấu trúc đường kẻ của bảng nổi rõ hơn, còn nhiều phản hồi yếu quanh chữ đã bị loại. Edge map này phù hợp hơn để đưa vào Hough Transform ở bước tiếp theo.

## Why NMS & Hysteresis?

Ở slide trước, ta đã thấy Canny đi qua nhiều bước để tạo edge map cuối cùng. Trong đó, **Non-Maximum Suppression (NMS)** và **Hysteresis** là hai bước quan trọng nhất để hiểu cách Canny biến một gradient response còn thô thành edge map mảnh và đáng tin hơn.

Hai bước này giải quyết hai vấn đề khác nhau. **NMS** xử lý việc một boundary xuất hiện thành một dải nhiều pixel, còn **Hysteresis** xử lý việc cùng một edge có thể có đoạn mạnh và đoạn yếu.

### Non-Maximum Suppression

Sau khi tính gradient magnitude, một edge thật thường không hiện thành đúng một pixel. Thay vào đó, nhiều pixel nằm gần cùng một boundary có thể đều có gradient lớn, nên edge xuất hiện thành một dải sáng khá dày.

**[CHÈN HÌNH: Non-Maximum Suppression (NMS)]**

*Hình. NMS giữ local maximum theo hướng gradient, từ đó thu một dải response dày thành edge mảnh hơn.*

Ở phần giữa của hình, ta xét một pixel hiện tại `q` và hai pixel `p`, `r` nằm ở hai phía theo **hướng gradient**. Đây chính là hướng cắt ngang edge, tức hướng mà intensity thay đổi mạnh nhất.

Nếu magnitude tại `q` lớn hơn cả `p` và `r`, thì `q` được xem là local maximum và được giữ lại. Nếu không, `q` bị đưa về 0.

Ví dụ:

`p = 38, q = 81, r = 55`

thì `q` được giữ vì `81` lớn hơn cả `38` và `55`.

Kết quả là những pixel nằm ở trung tâm của response được giữ, còn những pixel yếu hơn ở hai bên bị loại. Vì vậy, khi so panel **Before NMS** và **After NMS**, ta thấy một edge dày được thu lại thành một đường mảnh hơn.

Có một chi tiết quan trọng là gradient thực tế có thể có bất kỳ góc nào, chẳng hạn `37°`. Nhưng ảnh lại nằm trên một lưới pixel rời rạc, nên ta không phải lúc nào cũng có pixel nằm chính xác theo hướng đó. Vì vậy, hướng gradient thường được quy về một trong các hướng gần nhất như `0°`, `45°`, `90°` hoặc `135°`, rồi từ đó chọn `p` và `r` để so sánh.

Nói ngắn gọn, NMS trả lời câu hỏi:

> **"Trong dải response này, vị trí nào đại diện tốt nhất cho edge?"**

**Kết quả sau NMS:** edge mảnh hơn và vị trí boundary rõ hơn.

**Nó giúp gì:** các bước tìm line phía sau nhận được một tập edge pixels gọn hơn, thay vì nhiều pixel song song cùng mô tả một boundary.

---

### Hysteresis

Sau NMS, edge đã mảnh hơn nhưng vẫn chưa thể giữ tất cả các pixel còn lại như nhau, vì độ mạnh của chúng không đồng đều.

**[CHÈN HÌNH: Hysteresis]**

*Hình. Double threshold chia edge candidates thành strong, weak và rejected. Hysteresis chỉ giữ weak edges khi chúng còn kết nối với strong edges.*

Ở panel **Double threshold**, mỗi pixel được phân loại theo gradient magnitude:

- lớn hơn `High` → **strong edge**
- nằm giữa `Low` và `High` → **weak edge**
- nhỏ hơn `Low` → **rejected**

Trong hình, strong edges được tô **đỏ**, weak edges tô **vàng**, còn những pixel bị loại trở về nền đen.

Điểm quan trọng là weak edge không có nghĩa là edge sai. Nó chỉ có nghĩa là response tại đó chưa đủ mạnh để ta tin tưởng ngay.

Ví dụ, cùng một đường kẻ có thể có đoạn đỏ rất rõ nhưng một đoạn khác chỉ hiện vàng do contrast thấp hơn hoặc blur nhẹ. Nếu đoạn vàng đó nằm tiếp nối với đoạn đỏ, nó có lý do để được xem là một phần của cùng edge.

Hysteresis vì vậy kiểm tra **connectivity**. Một weak pixel được giữ nếu từ nó có thể đi qua các weak pixels lân cận để nối tới một strong edge. Nếu một cụm weak pixels đứng riêng và không nối với strong edge nào, cụm đó bị loại.

Trong hình, phần **Keep** minh họa một chuỗi pixel vàng nối tiếp từ strong edge màu đỏ nên toàn bộ chuỗi được giữ. Ngược lại, phần **Remove** cho thấy một nhóm pixel vàng đứng riêng nên bị loại.

Việc kiểm tra connectivity thường xét các pixel lân cận xung quanh, ví dụ 8-neighborhood. Điều quan trọng không phải nhớ loại connectivity nào, mà hiểu logic:

> **Weak edge chỉ được giữ khi nó có strong edge hỗ trợ về mặt liên kết.**

Hysteresis cũng không tự vẽ thêm pixel để nối mọi khoảng trống. Nó chỉ quyết định những weak pixels nào được giữ lại từ những pixel đã tồn tại sau threshold.

Nói ngắn gọn, Hysteresis trả lời câu hỏi:

> **"Trong những đoạn edge yếu còn lại, đoạn nào thực sự thuộc về một edge đáng tin?"**

**Kết quả sau Hysteresis:** weak edges có kết nối với strong edges được giữ, còn những response yếu đứng riêng bị loại.

**Nó giúp gì:** edge map cuối cùng vừa không mất các đoạn edge thật chỉ vì chúng yếu hơn, vừa giảm những phản hồi yếu không có hỗ trợ.

## From Edge Pixels to Straight Lines

Sau Canny, ta đã có một edge map gồm rất nhiều pixel trắng. Nhìn vào panel đầu tiên, ta có thể nhận ra các đường kẻ của bảng bằng mắt, nhưng với máy tính thì kết quả lúc này vẫn chỉ là **một tập các edge pixels riêng lẻ**.

**[CHÈN HÌNH: Canny edge pixels → aligned edge pixels → Hough line segments]**

*Hình. Canny cho các edge pixels, sau đó Hough tìm những pixel thẳng hàng và biểu diễn chúng thành các line segments.*

Ở panel **1. Canny edge pixels**, mỗi pixel trắng chỉ cho biết tại vị trí đó có một thay đổi intensity đủ mạnh để được xem là edge. Nó chưa nói rằng pixel đó thuộc đường ngang nào, đường dọc nào, hay có liên quan tới những pixel ở xa hơn hay không.

Sang panel **2. Aligned edge pixels**, ta minh họa ý tưởng mà Hough cần tìm: nhiều edge pixels cùng nằm gần trên một hướng có thể thuộc về cùng một đường. Trong hình, các pixel màu cam nằm dọc theo một đường ngang, còn các pixel màu cyan nằm dọc theo một đường dọc.

Điểm quan trọng là ta không muốn xử lý từng pixel này riêng lẻ. Với deskew, thứ ta thực sự cần là một đối tượng có **hướng rõ ràng**, để có thể nói đường đó đang nằm ngang, thẳng đứng hay bị nghiêng bao nhiêu độ.

Đó là vai trò của **Hough Transform**.

Ở panel **3. Hough line segments**, các nhóm edge pixels thẳng hàng được biểu diễn thành những đoạn thẳng rõ ràng. Các line ngang được tô màu cam và các line dọc được tô cyan.

Từ đây, thay vì làm việc với hàng trăm pixel của một đường kẻ, ta chỉ cần làm việc với một line segment có vị trí và hướng xác định.

Có thể hiểu ngắn gọn:

> **Canny tìm “điểm nào là edge”.**
>
> **Hough tìm “những edge points nào cùng tạo thành một đường”.**

Đây là bước chuyển quan trọng cho deskew, vì góc nghiêng của trang được ước lượng từ **hướng của các đường thẳng**, chứ không phải từ từng edge pixel riêng lẻ.

## Why $(\rho, \theta)$ instead of $y = ax + b$?

Trước khi nói Hough vote như thế nào, ta cần chốt một câu hỏi cơ bản hơn:

> **Một đường thẳng sẽ được mô tả bằng những giá trị nào?**

Cách quen thuộc nhất là:

$$

y = ax + b

$$

Trong đó $a$ là độ dốc của đường thẳng và $b$ là vị trí nó cắt trục $y$.

Cách biểu diễn này hoạt động tốt với nhiều đường thông thường, nhưng bắt đầu gặp vấn đề khi đường tiến gần phương thẳng đứng. Khi góc của đường tiến gần $90^\circ$, độ dốc $a$ tăng rất lớn. Với một đường thẳng đứng hoàn toàn, $a$ không còn xác định được.

**[CHÈN HÌNH: Why $(\rho, \theta)$ instead of $y = ax + b$?]**

*Hình. Dạng $y = ax + b$ trở nên không ổn định với đường gần thẳng đứng, trong khi $(\rho, \theta)$ vẫn biểu diễn được các đường theo cùng một cách.*

Ở phần bên trái của hình, ta có thể thấy sự thay đổi này khá rõ. Một đường ngang có $a = 0$, một đường nghiêng $45^\circ$ có $a = 1$, nhưng khi góc tăng lên $89.9^\circ$, độ dốc đã trở nên rất lớn. Đến $90^\circ$, đường thẳng đứng không còn biểu diễn thuận tiện bằng $y = ax + b$.

Hough vì vậy dùng một cách mô tả khác:

$$

\rho = x\cos\theta + y\sin\theta

$$

Ở đây, ta không mô tả đường bằng slope nữa. Thay vào đó, ta dựng một đoạn thẳng từ gốc tọa độ đi **vuông góc** tới đường cần biểu diễn.

Hai giá trị cần nhớ là:

- $\rho$: khoảng cách có dấu từ gốc tọa độ tới đường theo phương vuông góc.
- $\theta$: góc của đoạn vuông góc đó so với trục $x$.

Điểm rất dễ nhầm là:

> **$\theta$ là góc của đường pháp tuyến, không phải góc của chính đường thẳng.**

Ví dụ, với đường:

$$

x = 5

$$

đường này nằm thẳng đứng ở bên phải gốc tọa độ. Đường vuông góc ngắn nhất từ origin tới nó nằm theo phương ngang, nên:

$$

\theta = 0^\circ,\qquad \rho = 5

$$

Tương tự, với:

$$

x = -3

$$

nếu vẫn giữ cùng hướng pháp tuyến, ta có:

$$

\theta = 0^\circ,\qquad \rho = -3

$$

Dấu của $\rho$ giúp phân biệt đường nằm về phía nào so với origin theo hướng pháp tuyến đang xét. Còn độ lớn:

$$

|\rho|

$$

cho biết khoảng cách hình học từ origin tới đường.

Điểm quan trọng là với $(\rho, \theta)$, cả đường ngang, đường nghiêng và đường thẳng đứng đều được mô tả theo **cùng một cách**, không gặp trường hợp slope tăng vô hạn.

Đây là lý do representation này phù hợp với Hough Transform: thuật toán có thể tìm line bằng cách tìm các cặp $(\rho, \theta)$ mà không phải xử lý riêng đường thẳng đứng.

## One Edge Pixel → Many Possible Lines

Sau khi biết Hough dùng cặp $(\rho, \theta)$ để biểu diễn một đường thẳng, bước tiếp theo là hiểu **một edge pixel sẽ đóng góp như thế nào**.

Giả sử ta có một edge pixel tại vị trí:

$$

(x, y)

$$

Chỉ từ một pixel duy nhất, ta chưa thể biết chính xác đường nào đi qua nó, vì thực tế có rất nhiều đường thẳng với các hướng khác nhau đều có thể đi qua cùng một điểm đó.

**[CHÈN HÌNH: One edge pixel → many possible lines → one sinusoid in Hough Space]**

*Hình. Một edge pixel không xác định duy nhất một line. Nó tương ứng với nhiều line khả dĩ, và các line này tạo thành một sinusoid trong Hough Space.*

Ở panel đầu tiên, $(x, y)$ chỉ đơn giản là một vị trí trong ảnh.

Sang panel thứ hai, ta thấy nhiều đường với các hướng khác nhau đều có thể đi qua đúng pixel này. Với mỗi hướng $\theta$, ta tính được một giá trị $\rho$ tương ứng từ:

$$

\rho = x\cos\theta + y\sin\theta

$$

Nghĩa là mỗi giá trị $\theta$ tạo ra một cặp:

$$

(\rho, \theta)

$$

và mỗi cặp đó đại diện cho **một candidate line** có thể đi qua pixel hiện tại.

Nếu tiếp tục thay đổi $\theta$ qua nhiều giá trị khác nhau, ta thu được rất nhiều cặp $(\rho, \theta)$. Khi vẽ các cặp này trong Hough Space, chúng tạo thành một đường cong dạng sinusoid.

Do đó có thể hiểu:

> **Một point trong image space → một sinusoid trong Hough Space.**

Điểm quan trọng là sinusoid này **không phải một đường nằm trong ảnh gốc**. Nó chỉ biểu diễn tập hợp tất cả các line mà edge pixel đó có thể thuộc về.

Nói theo cách của Hough:

> **Một edge pixel không vote cho một line duy nhất. Nó vote cho nhiều candidate lines.**

Ở thời điểm này ta vẫn chưa biết candidate nào là line thật. Muốn xác định được điều đó, ta cần xem **nhiều edge pixels khác có cùng vote cho một candidate line hay không**.

Đó chính là ý dẫn sang slide tiếp theo: khi nhiều edge pixels thật sự nằm trên cùng một đường, các sinusoid của chúng sẽ cùng hội tụ tại một điểm chung trong Hough Space.

## Collinear Points → Intersection in Hough Space

Ở slide trước, ta đã thấy **một edge pixel duy nhất** có thể thuộc về rất nhiều đường khác nhau, nên nó tạo ra một sinusoid trong Hough Space.

Bây giờ xét trường hợp có **nhiều edge pixels cùng nằm trên một đường thẳng**.

**[CHÈN HÌNH: Collinear points → intersection in Hough Space]**

*Hình. Các edge pixels cùng nằm trên một line tạo ra các sinusoid khác nhau nhưng cùng giao tại một cặp $(\rho, \theta)$.*

Ở phía trái của hình, bốn điểm:

$$

(x_1, y_1),\quad

(x_2, y_2),\quad

(x_3, y_3),\quad

(x_4, y_4)

$$

cùng nằm trên một đường thẳng.

Mỗi điểm vẫn có thể thuộc về nhiều candidate lines, nên mỗi điểm tạo ra một sinusoid riêng trong Hough Space.

Điểm quan trọng nằm ở chỗ: vì bốn pixel này **thật sự cùng thuộc một line**, nên tồn tại một cặp:

$$

(\rho^*, \theta^*)

$$

mô tả đúng line đó.

Khi thử đúng $\theta^*$, cả bốn điểm đều cho cùng một giá trị $\rho^*$.

Vì vậy, các sinusoid của chúng sẽ cùng đi qua một điểm chung:

$$

(\rho^*, \theta^*)

$$

Điểm giao này chính là biểu diễn của đường thẳng mà các edge pixels đang cùng nằm trên.

Có thể hiểu rất trực quan:

> **Một pixel tạo ra nhiều khả năng. Nhiều pixel thẳng hàng cùng xác nhận một khả năng chung.**

Nếu các pixel không cùng nằm trên một line, các sinusoid của chúng sẽ không hội tụ rõ ràng tại cùng một điểm.

Đây là insight quan trọng nhất của Hough Transform:

> **Các edge pixels thẳng hàng sẽ cùng “đồng ý” về một cặp $(\rho, \theta)$.**

Ở mức lý thuyết, ta nhìn thấy điều đó như một **intersection** của nhiều sinusoid. Nhưng trong implementation thực tế, ta không cần vẽ các sinusoid rồi tìm giao điểm bằng mắt.

Thay vào đó, mỗi pixel sẽ vote vào một bảng đếm. Nếu nhiều pixel cùng vote cho cùng một cặp $(\rho, \theta)$, vị trí đó sẽ nhận rất nhiều vote và trở thành một **peak**.

Đó chính là nội dung của slide tiếp theo.

## Hough Space, Voting & Peaks

## Why $(\rho, \theta)$ instead of $y = ax + b$?

Trước khi nói Hough vote như thế nào, ta cần chốt một câu hỏi cơ bản hơn:

> **Một đường thẳng sẽ được mô tả bằng những giá trị nào?**

Cách quen thuộc nhất là:

$$

y = ax + b

$$

Trong đó $a$ là độ dốc của đường thẳng và $b$ là vị trí nó cắt trục $y$.

Cách biểu diễn này hoạt động tốt với nhiều đường thông thường, nhưng bắt đầu gặp vấn đề khi đường tiến gần phương thẳng đứng. Khi góc của đường tiến gần $90^\circ$, độ dốc $a$ tăng rất lớn. Với một đường thẳng đứng hoàn toàn, $a$ không còn xác định được.

**[CHÈN HÌNH: Why $(\rho, \theta)$ instead of $y = ax + b$?]**

*Hình. Dạng $y = ax + b$ trở nên không ổn định với đường gần thẳng đứng, trong khi $(\rho, \theta)$ vẫn biểu diễn được các đường theo cùng một cách.*

Ở phần bên trái của hình, ta có thể thấy sự thay đổi này khá rõ. Một đường ngang có $a = 0$, một đường nghiêng $45^\circ$ có $a = 1$, nhưng khi góc tăng lên $89.9^\circ$, độ dốc đã trở nên rất lớn. Đến $90^\circ$, đường thẳng đứng không còn biểu diễn thuận tiện bằng $y = ax + b$.

Hough vì vậy dùng một cách mô tả khác:

$$

\rho = x\cos\theta + y\sin\theta

$$

Ở đây, ta không mô tả đường bằng slope nữa. Thay vào đó, ta dựng một đoạn thẳng từ gốc tọa độ đi **vuông góc** tới đường cần biểu diễn.

Hai giá trị cần nhớ là:

- $\rho$: khoảng cách có dấu từ gốc tọa độ tới đường theo phương vuông góc.
- $\theta$: góc của đoạn vuông góc đó so với trục $x$.

Điểm rất dễ nhầm là:

> **$\theta$ là góc của đường pháp tuyến, không phải góc của chính đường thẳng.**

Ví dụ, với đường:

$$

x = 5

$$

đường này nằm thẳng đứng ở bên phải gốc tọa độ. Đường vuông góc ngắn nhất từ origin tới nó nằm theo phương ngang, nên:

$$

\theta = 0^\circ,\qquad \rho = 5

$$

Tương tự, với:

$$

x = -3

$$

nếu vẫn giữ cùng hướng pháp tuyến, ta có:

$$

\theta = 0^\circ,\qquad \rho = -3

$$

Dấu của $\rho$ giúp phân biệt đường nằm về phía nào so với origin theo hướng pháp tuyến đang xét. Còn độ lớn:

$$

|\rho|

$$

cho biết khoảng cách hình học từ origin tới đường.

Điểm quan trọng là với $(\rho, \theta)$, cả đường ngang, đường nghiêng và đường thẳng đứng đều được mô tả theo **cùng một cách**, không gặp trường hợp slope tăng vô hạn.

Đây là lý do representation này phù hợp với Hough Transform: thuật toán có thể tìm line bằng cách tìm các cặp $(\rho, \theta)$ mà không phải xử lý riêng đường thẳng đứng.

### Takeaway

**$(\rho, \theta)$ gives Hough a stable way to represent any straight line, including vertical lines.**

## One Edge Pixel → Many Possible Lines

Sau khi biết Hough dùng cặp $(\rho, \theta)$ để biểu diễn một đường thẳng, bước tiếp theo là hiểu **một edge pixel sẽ đóng góp như thế nào**.

Giả sử ta có một edge pixel tại vị trí:

$$

(x, y)

$$

Chỉ từ một pixel duy nhất, ta chưa thể biết chính xác đường nào đi qua nó, vì thực tế có rất nhiều đường thẳng với các hướng khác nhau đều có thể đi qua cùng một điểm đó.

**[CHÈN HÌNH: One edge pixel → many possible lines → one sinusoid in Hough Space]**

*Hình. Một edge pixel không xác định duy nhất một line. Nó tương ứng với nhiều line khả dĩ, và các line này tạo thành một sinusoid trong Hough Space.*

Ở panel đầu tiên, $(x, y)$ chỉ đơn giản là một vị trí trong ảnh.

Sang panel thứ hai, ta thấy nhiều đường với các hướng khác nhau đều có thể đi qua đúng pixel này. Với mỗi hướng $\theta$, ta tính được một giá trị $\rho$ tương ứng từ:

$$

\rho = x\cos\theta + y\sin\theta

$$

Nghĩa là mỗi giá trị $\theta$ tạo ra một cặp:

$$

(\rho, \theta)

$$

và mỗi cặp đó đại diện cho **một candidate line** có thể đi qua pixel hiện tại.

Nếu tiếp tục thay đổi $\theta$ qua nhiều giá trị khác nhau, ta thu được rất nhiều cặp $(\rho, \theta)$. Khi vẽ các cặp này trong Hough Space, chúng tạo thành một đường cong dạng sinusoid.

Do đó có thể hiểu:

> **Một point trong image space → một sinusoid trong Hough Space.**

Điểm quan trọng là sinusoid này **không phải một đường nằm trong ảnh gốc**. Nó chỉ biểu diễn tập hợp tất cả các line mà edge pixel đó có thể thuộc về.

Nói theo cách của Hough:

> **Một edge pixel không vote cho một line duy nhất. Nó vote cho nhiều candidate lines.**

Ở thời điểm này ta vẫn chưa biết candidate nào là line thật. Muốn xác định được điều đó, ta cần xem **nhiều edge pixels khác có cùng vote cho một candidate line hay không**.

Đó chính là ý dẫn sang slide tiếp theo: khi nhiều edge pixels thật sự nằm trên cùng một đường, các sinusoid của chúng sẽ cùng hội tụ tại một điểm chung trong Hough Space.

### Takeaway

**One edge pixel votes for many possible lines. Its votes form a sinusoid in Hough Space.**

## Collinear Points → Intersection in Hough Space

Ở slide trước, ta đã thấy **một edge pixel duy nhất** có thể thuộc về rất nhiều đường khác nhau, nên nó tạo ra một sinusoid trong Hough Space.

Bây giờ xét trường hợp có **nhiều edge pixels cùng nằm trên một đường thẳng**.

**[CHÈN HÌNH: Collinear points → intersection in Hough Space]**

*Hình. Các edge pixels cùng nằm trên một line tạo ra các sinusoid khác nhau nhưng cùng giao tại một cặp $(\rho, \theta)$.*

Ở phía trái của hình, bốn điểm:

$$

(x_1, y_1),\quad

(x_2, y_2),\quad

(x_3, y_3),\quad

(x_4, y_4)

$$

cùng nằm trên một đường thẳng.

Mỗi điểm vẫn có thể thuộc về nhiều candidate lines, nên mỗi điểm tạo ra một sinusoid riêng trong Hough Space.

Điểm quan trọng nằm ở chỗ: vì bốn pixel này **thật sự cùng thuộc một line**, nên tồn tại một cặp:

$$

(\rho^*, \theta^*)

$$

mô tả đúng line đó.

Khi thử đúng $\theta^*$, cả bốn điểm đều cho cùng một giá trị $\rho^*$.

Vì vậy, các sinusoid của chúng sẽ cùng đi qua một điểm chung:

$$

(\rho^*, \theta^*)

$$

Điểm giao này chính là biểu diễn của đường thẳng mà các edge pixels đang cùng nằm trên.

Có thể hiểu rất trực quan:

> **Một pixel tạo ra nhiều khả năng. Nhiều pixel thẳng hàng cùng xác nhận một khả năng chung.**

Nếu các pixel không cùng nằm trên một line, các sinusoid của chúng sẽ không hội tụ rõ ràng tại cùng một điểm.

Đây là insight quan trọng nhất của Hough Transform:

> **Các edge pixels thẳng hàng sẽ cùng “đồng ý” về một cặp $(\rho, \theta)$.**

Ở mức lý thuyết, ta nhìn thấy điều đó như một **intersection** của nhiều sinusoid. Nhưng trong implementation thực tế, ta không cần vẽ các sinusoid rồi tìm giao điểm bằng mắt.

Thay vào đó, mỗi pixel sẽ vote vào một bảng đếm. Nếu nhiều pixel cùng vote cho cùng một cặp $(\rho, \theta)$, vị trí đó sẽ nhận rất nhiều vote và trở thành một **peak**.

Đó chính là nội dung của slide tiếp theo.

### Takeaway

**Collinear edge pixels produce sinusoids that intersect at the same $(\rho, \theta)$, revealing the line they share.**

## Voting, Accumulator and Peaks

Ở slide trước, ta đã thấy nhiều edge pixels cùng nằm trên một line sẽ cùng “đồng ý” về một cặp $(\rho, \theta)$.

Trong implementation thực tế, Hough không cần vẽ toàn bộ các sinusoid rồi tìm giao điểm. Thay vào đó, nó biến việc tìm line thành một bài toán **đếm vote**.

**[CHÈN HÌNH: Collinear edge pixels → Accumulator table → Peak → Detected line]**

*Hình. Các edge pixels cùng hỗ trợ một line sẽ làm ô tương ứng trong accumulator nhận nhiều vote hơn và tạo thành peak.*

Ở panel đầu tiên, ta có một số edge pixels cùng nằm trên một đường thẳng. Mỗi pixel có thể thuộc về nhiều candidate lines khác nhau, nên nó sẽ vote cho nhiều cặp $(\rho, \theta)$ có thể đi qua nó.

Các vote này được lưu trong một bảng gọi là **accumulator**.

Có thể hình dung mỗi ô trong bảng tương ứng với một candidate line cụ thể:

- Hàng xác định một giá trị $\rho$.
- Cột xác định một giá trị $\theta$.
- Giá trị trong ô cho biết có bao nhiêu edge pixels đang ủng hộ candidate line đó.

Ví dụ, ô tại:

$$

(\rho_3, \theta_3)

$$

có giá trị:

$$

4

$$

Điều này có nghĩa là bốn edge pixels đang cùng ủng hộ line được mô tả bởi cặp:

$$

(\rho_3, \theta_3)

$$

Những candidate lines sai thường chỉ nhận được một vài vote rải rác. Ngược lại, nếu nhiều edge pixels thật sự cùng nằm trên một line, vote của chúng sẽ cùng dồn vào một ô hoặc một vùng rất gần nhau trong accumulator.

Ô có số vote lớn nổi bật lên như một **peak**.

Trong hình, peak nằm tại:

$$

(\rho^*, \theta^*) = (\rho_3, \theta_3)

$$

Cặp giá trị này chính là tham số của line được nhiều edge pixels cùng ủng hộ nhất.

Từ peak đó, ta có thể quay trở lại image space và biểu diễn line tương ứng.

Điểm quan trọng là Hough đã biến một bài toán hình học:

> “Những edge pixels nào cùng nằm trên một line?”

thành một bài toán đếm đơn giản hơn:

> “Candidate line nào nhận được nhiều vote nhất?”

Đây là ý nghĩa của accumulator. Nó không lưu pixel của ảnh, mà lưu **mức độ ủng hộ dành cho từng candidate line**.

Nếu một ảnh có nhiều line rõ ràng, accumulator sẽ có nhiều peak tương ứng. Sau đó, một threshold về số vote được dùng để quyết định peak nào đủ mạnh để được xem là detected line.

### Takeaway

**Voting turns geometric agreement into a counting problem: strong peaks in the accumulator correspond to likely straight lines.**

## 4.2 Contrast Enhancement & Binarization

## Why Contrast Enhancement & Binarization?

---

## From Image Intensity to Histogram

Ở slide trước, ta đã thấy ảnh xám có thể chứa những vùng chữ, đường kẻ và nền chưa tách biệt rõ. Để hiểu CLAHE và Otsu hoạt động như thế nào, trước hết cần nhìn ảnh theo một cách khác: **không chỉ xem pixel nằm ở đâu, mà còn xem các mức sáng phân bố như thế nào trong toàn ảnh**.

Trong ảnh grayscale, mỗi pixel có một **intensity value**, thường nằm trong khoảng:

$$

0 \rightarrow 255

$$

Có thể hiểu đơn giản:

- `0` là đen
- giá trị ở giữa là các mức xám
- `255` là trắng

Nếu ta lấy toàn bộ pixel trong ảnh rồi đếm xem có bao nhiêu pixel mang từng mức intensity, ta thu được một **histogram**.

**[CHÈN HÌNH: Grayscale image → intensity values → histogram]**

*Hình. Histogram cho biết có bao nhiêu pixel xuất hiện ở từng mức intensity trong ảnh grayscale.*

Trên histogram:

- trục X là **intensity**
- trục Y là **số lượng pixel**

Ví dụ, nếu cột tại intensity `220` rất cao, điều đó có nghĩa là trong ảnh có rất nhiều pixel sáng gần mức `220`. Nếu vùng intensity thấp có nhiều pixel, ảnh chứa nhiều vùng tối hơn.

Điểm quan trọng là histogram **không cho biết pixel nằm ở đâu trong ảnh**. Nó chỉ cho biết các mức sáng đang xuất hiện nhiều hay ít.

Vì vậy:

> Ảnh cho ta biết **pixel ở vị trí nào**.
>
> Histogram cho ta biết **các mức sáng đang phân bố ra sao**.

Điều này rất hữu ích cho hai bước tiếp theo.

- Với **CLAHE**, ta quan tâm đến việc các intensity đang bị dồn vào một khoảng hẹp hay đã được trải rộng đủ để tạo contrast rõ hơn.
- Với **Otsu**, ta quan tâm đến việc có thể chọn một threshold `T` nào đó để chia các pixel thành hai nhóm, chẳng hạn foreground và background, sao cho sự phân tách là tốt nhất theo tiêu chí của thuật toán.

Một điều cần lưu ý là histogram của ảnh tài liệu thực tế **không nhất thiết có hai peak đẹp và tách biệt rõ ràng**. Nền giấy, vùng bóng, noise và chữ có thể làm các nhóm intensity chồng lấn lên nhau. Vì vậy histogram ở slide này chỉ nên được dùng để hiểu cách intensity được phân bố, chưa phải để kết luận ngay đâu là foreground và đâu là background.

## From Histogram to CDF

Histogram cho biết có bao nhiêu pixel xuất hiện ở từng mức intensity. Tuy nhiên, để Histogram Equalization biết **mỗi mức sáng nên được ánh xạ sang đâu**, chỉ nhìn số pixel ở từng bin riêng lẻ là chưa đủ. Ta cần biết **đến một mức sáng nào đó, đã tích lũy bao nhiêu pixel**.

Giả sử ảnh có tổng cộng $N$ pixel và $n_b$ là số pixel nằm ở bin $b$. Ta chuẩn hóa histogram thành tỷ lệ:

$$

h[b] = \frac{n_b}{N}

$$

$h[b]$ cho biết **tỷ lệ pixel của ảnh đang nằm đúng tại intensity $b$**.

Ví dụ, nếu:

$$

h[50] = 0.08

$$

thì khoảng $8\\%$ pixel của ảnh có intensity bằng $50$.

Từ đây, ta cộng dồn các giá trị histogram từ mức sáng thấp nhất đến $b$:

$$

H[b] = \sum\_{k=0}^{b} h[k]

$$

$H[b]$ được gọi là **Cumulative Distribution Function (CDF)**. Có thể hiểu đơn giản, nó trả lời câu hỏi:

> **“Có bao nhiêu phần trăm pixel có intensity nhỏ hơn hoặc bằng $b$?”**

**[CHÈN HÌNH: Histogram → Density Histogram → Cumulative Histogram]**

*Hình. Histogram được chuẩn hóa thành tỷ lệ pixel ở từng mức sáng, sau đó cộng dồn để tạo CDF.*

Ví dụ, nếu:

$$

H[50] = 0.52

$$

thì khoảng $52\\%$ pixel của ảnh có intensity nhỏ hơn hoặc bằng $50$.

Điểm quan trọng nằm ở **độ dốc của CDF**.

Nếu một khoảng intensity chứa rất nhiều pixel, khi đi qua khoảng đó $H[b]$ sẽ tăng nhanh. Ngược lại, nếu một khoảng intensity có ít pixel, CDF tăng chậm hơn.

Do đó:

- **histogram cao** ở một vùng → CDF tăng nhanh
- **histogram thấp** → CDF tăng chậm

Đây chính là thông tin mà Histogram Equalization cần. Những vùng intensity đang có nhiều pixel sẽ làm CDF thay đổi nhanh hơn, từ đó ở bước mapping sau, các mức sáng trong vùng đó được tách ra rộng hơn.

## CDF → New Intensity Values

CDF cho biết đến mỗi mức intensity, đã tích lũy bao nhiêu phần trăm pixel của ảnh. Histogram Equalization dùng chính giá trị tích lũy này để quyết định **mức sáng mới** cho từng intensity cũ.

Giả sử ảnh có $L$ mức xám. Với ảnh 8-bit thông thường:

$$

L = 256

$$

Intensity mới được tính theo:

$$

s = (L-1)H[r]

$$

Trong đó:

- $r$ là intensity ban đầu
- $H[r]$ là CDF tại intensity đó
- $s$ là intensity mới sau khi equalize

**[CHÈN HÌNH: Gray Level → CDF → New Gray Level]**

*Hình. Histogram Equalization dùng CDF để ánh xạ mỗi intensity ban đầu sang một intensity mới.*

Ví dụ, nếu ảnh chỉ có $8$ mức xám thì:

$$

L = 8

$$

Giả sử tại gray level $r = 2$ ta có:

$$

H[2] = 0.36

$$

thì:

$$

s = (8-1)\times0.36 = 2.52

$$

Sau khi đưa về một gray level rời rạc phù hợp, intensity mới sẽ nằm gần mức $3$.

Điểm quan trọng không nằm ở phép nhân này, mà ở **cách CDF thay đổi theo histogram**.

Nếu một vùng intensity có rất nhiều pixel, CDF tăng nhanh trong vùng đó. Khi đưa qua công thức mapping, các gray levels nằm gần nhau trong vùng đông pixel sẽ được đẩy ra các giá trị đầu ra cách xa nhau hơn.

Ngược lại, ở vùng intensity có ít pixel, CDF thay đổi chậm hơn nên các mức sáng đầu ra cũng không bị kéo giãn nhiều.

Có thể hiểu ngắn gọn:

> **Vùng intensity càng đông pixel thì CDF càng tăng nhanh, nên các mức sáng ở đó được trải ra mạnh hơn.**

Đây là lý do Histogram Equalization giúp tăng contrast. Những mức sáng trước đây nằm quá gần nhau được ánh xạ ra xa nhau hơn, khiến các vùng trong ảnh dễ phân biệt hơn.

Sau khi remap toàn bộ gray levels, histogram đầu ra thường trải rộng hơn trên dải intensity. Tuy nhiên, nó không nhất thiết trở thành một histogram phẳng hoàn hảo, đặc biệt với ảnh số có số pixel hữu hạn và các gray levels rời rạc.

---

## The Limitation of Global Equalization

Histogram Equalization tăng contrast bằng cách dùng **một mapping chung cho toàn bộ ảnh**. Cách này hoạt động tốt khi điều kiện sáng tối trên ảnh tương đối đồng đều, vì mọi pixel đều được điều chỉnh theo cùng một quy tắc.

Vấn đề xuất hiện khi độ sáng thay đổi theo từng vùng. Một phần của tài liệu có thể tối hơn do bóng hoặc chất lượng scan, trong khi vùng khác lại sáng hơn. Khi đó, cùng một mapping toàn cục phải xử lý cả hai vùng cùng lúc.

**[CHÈN HÌNH: document có vùng tối và vùng sáng → global equalization → một vùng được cải thiện nhưng vùng khác chưa phù hợp]**

*Hình. Global Equalization sử dụng một mapping cho toàn ảnh, nên khó thích nghi khi các vùng có điều kiện sáng tối khác nhau.*

Giả sử phía trái của trang khá tối còn phía phải sáng hơn. Nếu mapping được điều chỉnh để làm rõ vùng tối, vùng sáng có thể bị kéo contrast quá mạnh. Ngược lại, nếu mapping phù hợp với vùng sáng, chữ và đường kẻ ở vùng tối vẫn có thể chưa tách rõ khỏi nền.

Một vấn đề khác là những biến động nhỏ của nền cũng có thể bị khuếch đại. Khi contrast được tăng trên toàn ảnh, không chỉ chữ và đường kẻ được làm nổi bật mà cả texture giấy hoặc noise trong một số vùng cũng có thể trở nên rõ hơn.

Điểm mấu chốt là:

> **Một mapping chung không biết vùng nào đang tối hơn, vùng nào đang sáng hơn.**

Vì vậy, khi illumination thay đổi theo vị trí, global equalization có thể không đủ linh hoạt để cải thiện contrast đồng đều trên toàn trang.

## CLAHE: Local Contrast Enhancement

Khi độ sáng thay đổi theo từng vùng, một mapping chung cho toàn ảnh không còn đủ linh hoạt. Ý tưởng tự nhiên lúc này là **điều chỉnh contrast theo từng vùng nhỏ**, để mỗi khu vực được xử lý dựa trên phân bố intensity của chính nó.

CLAHE thực hiện điều này bằng cách chia ảnh thành nhiều **tiles**, tức các vùng nhỏ có kích thước cố định. Với mỗi tile, histogram được tính riêng và một mapping riêng được tạo ra để tăng local contrast.

**[CHÈN HÌNH: Image → Tiles → Local Histograms → Local Equalization]**

*Hình. CLAHE chia ảnh thành nhiều vùng nhỏ và điều chỉnh contrast theo phân bố intensity của từng vùng.*

Nhờ cách xử lý cục bộ này, một vùng tối có thể được tăng contrast mạnh hơn, trong khi một vùng vốn đã sáng rõ không cần chịu cùng một phép biến đổi. Điều này phù hợp hơn với ảnh tài liệu có illumination thay đổi theo vị trí.

Tuy nhiên, nếu chỉ equalize từng tile độc lập, một vấn đề mới xuất hiện: những tile có histogram rất tập trung có thể bị tăng contrast quá mạnh. Khi đó, không chỉ chữ và đường kẻ nổi lên mà noise hoặc texture nền cũng có thể bị khuếch đại.

Để hạn chế điều này, CLAHE dùng **clip limit**. Những bin histogram vượt quá giới hạn sẽ bị cắt bớt, phần vượt quá được phân phối lại cho các bin khác. Mục tiêu là tránh để một nhóm intensity quá lớn chi phối hoàn toàn mapping của tile.

Có thể hiểu ngắn gọn:

> **Clip limit giới hạn mức contrast mà một tile được phép khuếch đại.**

Sau khi mỗi tile có mapping riêng, vẫn còn một vấn đề nữa. Nếu áp dụng mapping của từng tile một cách tách biệt, ranh giới giữa các tile có thể trở nên nhìn thấy rõ.

Vì vậy, CLAHE dùng **interpolation** giữa các tile lân cận để tạo chuyển tiếp mượt hơn. Một pixel gần ranh giới không chỉ chịu ảnh hưởng từ đúng một tile, mà được tính từ các mapping xung quanh theo vị trí của nó.

Như vậy, CLAHE có ba ý chính:

- chia ảnh thành **tiles** để xử lý cục bộ
- dùng **clip limit** để tránh khuếch đại quá mạnh
- dùng **interpolation** để làm mượt ranh giới giữa các tiles

Trong pipeline hiện tại, CLAHE được dùng với `tileGridSize = (8, 8)` và `clipLimit = 2.0`. Hai tham số này không phải quy luật chung, mà là lựa chọn implementation cụ thể.

Kết quả của CLAHE vẫn là **ảnh grayscale**, chưa phải binary image. Nó chỉ làm cho foreground và background dễ tách hơn ở bước thresholding tiếp theo.

---

## From Grayscale to Binary: Why Threshold?

Sau CLAHE, ảnh vẫn là grayscale. Điều đó có nghĩa mỗi pixel vẫn có thể nhận nhiều mức sáng khác nhau từ tối đến sáng. Với con người, ta vẫn dễ nhìn ra đâu là chữ, đâu là đường kẻ, đâu là nền. Nhưng với các bước xử lý hình học phía sau, biểu diễn như vậy vẫn còn quá mơ hồ.

Mục tiêu của thresholding là biến ảnh nhiều mức xám thành **hai nhóm rõ ràng hơn**:

- một nhóm đại diện cho **foreground**, tức chữ và đường kẻ cần giữ
- một nhóm đại diện cho **background**

Ta chọn một ngưỡng $T$. Với mỗi pixel có intensity $I(x,y)$, ta quyết định nó thuộc nhóm nào bằng cách so sánh với $T$.

Ví dụ với tài liệu chữ tối trên nền sáng:

$$

I(x,y) < T

$$

thì pixel có thể được xem là foreground, còn pixel sáng hơn được xem là background.

**[CHÈN HÌNH: Grayscale image → threshold $T$ → Binary image]**

*Hình. Thresholding biến nhiều mức intensity thành hai nhóm foreground và background.*

Điểm quan trọng là ảnh binary không còn giữ thông tin kiểu "pixel này hơi tối hơn pixel kia". Thay vào đó, mỗi pixel chỉ còn một quyết định rõ ràng:

> "Giữ pixel này như một phần của cấu trúc cần xử lý hay bỏ nó vào background?"

Điều này đặc biệt hữu ích cho các bước tìm đường kẻ phía sau. Khi table lines đã trở thành các pixel foreground rõ ràng, hệ thống có thể xử lý chúng như các hình dạng hình học thay vì phải liên tục cân nhắc nhiều mức xám.

Trong pipeline này, ảnh còn được **invert** để có quy ước thuận tiện hơn:

- background = $0$
- text và table lines = $255$

Như vậy, các cấu trúc cần giữ trở thành màu trắng trên nền đen, phù hợp hơn cho các phép morphology ở bước sau.

Vấn đề còn lại là:

> **Nên chọn threshold $T$ bằng bao nhiêu?**

Nếu $T$ quá thấp, một phần chữ hoặc đường kẻ có thể bị mất. Nếu $T$ quá cao, noise và background có thể bị giữ lại quá nhiều.

Vì vậy thay vì chọn $T$ thủ công, bước tiếp theo sử dụng **Otsu Thresholding** để tự động tìm một ngưỡng phù hợp từ phân bố intensity của ảnh.

## What Makes a Good Threshold?

Khi chọn một threshold $T$, histogram được chia thành hai class. Ví dụ với $T = 2$, các gray level $0, 1, 2$ thuộc class 1, còn $3, 4$ thuộc class 2.

Nhưng vấn đề không chỉ là chia histogram thành hai phần. Ta còn cần đánh giá xem **cách chia đó có tốt hay không**.

Một cách nhìn đầu tiên là **within-class variance**, tức mức độ phân tán của các intensity bên trong từng class.

$$

V_w = \sum\_{i=1}^{N} W_i\sigma_i^2

$$

Trong đó $W_i$ là tỷ lệ pixel thuộc class $i$, còn $\sigma_i^2$ là variance của các intensity trong class đó.

Nếu các pixel trong cùng một class có intensity gần nhau, variance của class sẽ nhỏ. Vì vậy:

> **$V_w$ càng nhỏ thì các class càng compact.**

Với ví dụ trên, histogram được chia thành hai class và ta thu được:

$$

V_w = W_1\sigma_1^2 + W_2\sigma_2^2 = 0.52777

$$

Một cách nhìn khác là **between-class variance**, tức mức độ tách biệt giữa hai class.

Với hai class:

$$

V_b = W_1W_2(\mu_1-\mu_2)^2

$$

Trong đó $\mu_1$ và $\mu_2$ là intensity trung bình của hai class.

Nếu trung bình của hai class nằm càng xa nhau, $V_b$ càng lớn. Vì vậy:

> **$V_b$ càng lớn thì hai class càng được phân tách rõ.**

Trong ví dụ này:

$$

V_b = 1.25

$$

Within-class variance và between-class variance không phải hai tiêu chí độc lập hoàn toàn. Chúng liên hệ thông qua total variance:

$$

V_T = V_w + V_b

$$

Vì histogram ban đầu không thay đổi khi ta thử các threshold khác nhau nên $V_T$ là hằng số. Do đó:

$$

\min V_w

\Longleftrightarrow

\max V_b

$$

Nói cách khác, một threshold tốt có thể được nhìn theo hai hướng tương đương:

> **Pixel trong từng class nên càng giống nhau càng tốt, đồng thời hai class nên càng khác nhau càng tốt.**

### Takeaway

**A good threshold produces compact classes with strong separation between them.**

## Otsu Thresholding: Choosing the Best $T$

Sau khi đã có tiêu chí để đánh giá một threshold, Otsu sử dụng tiêu chí đó để **tự động tìm $T$ phù hợp nhất**.

Ý tưởng khá trực tiếp. Thuật toán thử lần lượt các threshold có thể có. Với mỗi $T$, histogram được chia thành hai class rồi tính within-class variance $V_w$ hoặc between-class variance $V_b$.

Ví dụ, nếu thử:

$$

T = 0,1,2,3,4

$$

ta sẽ thu được một giá trị $V_w$ và $V_b$ tương ứng cho mỗi cách chia.

Trong slide, $T = 2$ minh họa một lần thử cụ thể:

- class 1 chứa gray level $0,1,2$
- class 2 chứa gray level $3,4$

Với cách chia này:

$$

V_w = 0.52777

$$

và:

$$

V_b = 1.25

$$

Nhưng Otsu không dừng lại ở $T = 2$. Thuật toán tiếp tục đánh giá các threshold khác rồi so sánh toàn bộ kết quả.

Trong bảng của ví dụ, tại $T = 1$:

$$

V_w = 0.38888

$$

là giá trị nhỏ nhất, đồng thời:

$$

V_b = 1.38888

$$

là giá trị lớn nhất.

Vì vậy threshold được chọn là:

$$

T^\* = 1

$$

Có thể viết quá trình lựa chọn dưới dạng:

$$

T^\* = \arg\min_T V_w(T)

$$

hoặc tương đương:

$$

T^\* = \arg\max_T V_b(T)

$$

Đó chính là điểm quan trọng của Otsu. Ta không cần tự đoán một threshold cố định. Thuật toán sử dụng histogram của chính ảnh để thử các cách chia và chọn cách phân tách hai class tốt nhất theo tiêu chí variance.

Sau khi tìm được $T$, threshold được áp dụng lên toàn bộ ảnh để tạo binary image. Trong pipeline này còn sử dụng binary inversion để có quy ước:

$$

\text{background} = 0

$$

$$

\text{text and table lines} = 255

$$

Do đó phần tiền xử lý có thể nối lại thành:

**CLAHE → Otsu Thresholding → Binary Inversion → Binary Image**

Binary image lúc này đã đưa chữ và các đường kẻ về foreground rõ ràng, tạo đầu vào cho bước tiếp theo là **Morphological Line Extraction**.

## 4.3 Table Grid Detection

## Morphological Line Extraction

## Why contours? From pixels to object geometry

Sau thresholding và morphology, ta thu được một binary mask: pixel trắng thuộc foreground, pixel đen thuộc background. Khi các đường ngang và dọc được ghép lại, chúng tạo thành một vùng foreground đại diện cho bảng.

Tuy nhiên, binary mask mới chỉ biểu diễn object ở mức pixel. Muốn xác định bảng nằm ở đâu, rộng bao nhiêu và cao bao nhiêu, hệ thống cần một biểu diễn hình học thuận tiện hơn.

Contour là đường bao của object, được biểu diễn như một chuỗi điểm có thứ tự chạy quanh biên. Nhờ đó, hệ thống có thể chuyển từ một vùng pixel sang một đối tượng hình học có vị trí, kích thước và diện tích rõ ràng.

**[CHÈN HÌNH: Joined Line Mask → External Boundary Pixels → Full Ordered Boundary → Candidate Bounding Box]**

*Hình. Từ line mask, hệ thống lần theo biên ngoài để tạo contour, rồi dùng contour đó để xác định bounding box của bảng.*

Trong hình:

1. **Joined line mask:** các đường ngang và dọc đã được ghép thành một vùng foreground liên thông.
2. **External boundary pixels:** các pixel nằm trên biên ngoài của vùng này được nhận diện.
3. **Full ordered boundary:** các điểm biên được sắp theo thứ tự chạy liên tục quanh object để tạo thành contour hoàn chỉnh.
4. **Candidate bounding box:** từ contour, hệ thống lấy hình chữ nhật bao ngoài để xác định vị trí và kích thước của bảng trên trang.

Trong bước định vị bảng, hệ thống chủ yếu quan tâm đến đường bao ngoài của toàn bộ bảng. Các đường kẻ và ô bên trong vẫn được giữ lại trong line mask để dùng cho bước khôi phục hàng, cột ở phía sau.

## Why Extract Lines from the Binary Image?

Sau Otsu và binary inversion, ảnh đã được đưa về hai giá trị rõ ràng:

$$

\text{background} = 0

$$

$$

\text{foreground} = 255

$$

Nhưng foreground lúc này vẫn chứa **nhiều loại cấu trúc khác nhau**. Chữ, số, ký tự và các đường kẻ của bảng đều xuất hiện dưới dạng pixel trắng.

Nếu nhìn vào một vùng bảng, ta có thể thấy:

- text tạo thành nhiều component nhỏ, hình dạng phức tạp
- table borders tạo thành các đoạn dài theo phương ngang hoặc phương dọc

**[CHÈN HÌNH: Binary Image với text và table lines cùng màu trắng]**

*Hình. Sau thresholding, text và table lines đều trở thành foreground nên vẫn chưa thể tách trực tiếp cấu trúc grid.*

Nếu xử lý toàn bộ foreground như nhau, các bước phía sau sẽ phải làm việc với cả chữ lẫn đường kẻ. Ví dụ, khi tìm contour, mỗi ký tự cũng có thể tạo ra một contour riêng, khiến rất khó xác định đâu là cấu trúc của bảng.

Điểm khác biệt quan trọng nằm ở **hình dạng**.

Table grid thường được tạo bởi:

- các đường dài theo horizontal direction
- các đường dài theo vertical direction
- các intersection giữa hai nhóm đường này

Trong khi đó, text thường không tạo thành những cấu trúc dài và liên tục theo một hướng cố định như vậy.

Vì thế, thay vì cố gắng nhận biết từng ký tự rồi loại bỏ chúng, ta có thể khai thác trực tiếp đặc điểm hình học của table grid:

> **Giữ lại các cấu trúc dài theo horizontal và vertical direction, đồng thời loại phần lớn foreground không có hình dạng đó.**

Kết quả mong muốn của bước này là tạo ra hai representation riêng:

$$

\text{Horizontal Mask}

$$

và

$$

\text{Vertical Mask}

$$

Trong đó mỗi mask chỉ giữ những line phù hợp với một hướng nhất định.

Từ hai mask này, ta có thể ghép lại để phục hồi phần lớn cấu trúc grid của bảng.

## Structuring Element: Shape, Origin, Fit & Hit

Trong Morphology, **Structuring Element** là một mẫu hình học nhỏ dùng để “thử” lên ảnh nhị phân. Có thể hiểu nó như một khuôn: thay vì nhìn toàn bộ object cùng lúc, ta đặt khuôn này lên từng vị trí trong ảnh để kiểm tra xem vùng lân cận quanh vị trí đó có khớp với điều kiện mong muốn hay không.

Điểm quan trọng là Structuring Element không chỉ cho biết **kích thước** vùng lân cận, mà còn cho biết **hình dạng** nào đang được quan tâm. Vì vậy, đổi Structuring Element cũng có nghĩa là đổi cách Morphology “nhìn” object.

Trong hình, hàng đầu cho thấy một số Structuring Element thường gặp.

- **3 × 3 square**: xét toàn bộ vùng lân cận 3 × 3.
- **Cross (4-neighborhood)**: chỉ nhấn mạnh bốn hướng trên, dưới, trái, phải.
- **Disk-like (8-neighborhood)**: bao quát đều hơn quanh tâm, gần với ý tưởng lân cận theo nhiều hướng.
- **Horizontal line**: ưu tiên các cấu trúc kéo dài theo phương ngang.
- **Vertical line**: ưu tiên các cấu trúc kéo dài theo phương dọc.

Như vậy, mỗi hình dạng sẽ phù hợp với một kiểu cấu trúc khác nhau. Nếu muốn kiểm tra một đoạn ngang dài, horizontal line sẽ tự nhiên hơn square. Nếu muốn kiểm tra quan hệ theo bốn hướng chính, cross sẽ phù hợp hơn.

Một thành phần luôn đi kèm với Structuring Element là **Origin**. Origin là điểm tham chiếu của Structuring Element, được vẽ bằng chấm đỏ trong hình. Khi trượt Structuring Element trên ảnh, origin chính là điểm đang “đứng” tại pixel hiện tại. Nói cách khác, mọi phép kiểm tra đều xoay quanh pixel mà origin đang trỏ tới.

Vì thế, khi nói “giữ lại pixel này” hay “bật pixel này”, thực chất ta đang nói đến pixel nằm tại vị trí của origin sau khi đặt Structuring Element lên ảnh.

Từ đây xuất hiện hai khái niệm nền tảng là **Fit** và **Hit**.

### Fit

**Fit** xảy ra khi **toàn bộ các ô active** của Structuring Element đều rơi vào foreground của ảnh. Trong hình, ví dụ **A: Fit** minh họa trường hợp này: phần màu cam được đặt lên object sao cho tất cả những ô mà Structuring Element yêu cầu đều nằm gọn trên vùng xanh.

Có thể hiểu đơn giản: Structuring Element “lọt hoàn toàn” vào trong object.

Fit là điều kiện chặt. Chỉ cần một phần active của Structuring Element rơi ra background thì không còn là Fit nữa. Vì vậy, Fit thường gắn với ý tưởng **giữ lại phần lõi**, tức những vùng đủ đầy và đủ rộng để chứa trọn Structuring Element.

### Hit

**Hit** xảy ra khi **ít nhất một ô active** của Structuring Element chạm vào foreground. Trong hình, ví dụ **B: Hit** cho thấy phần màu cam chỉ chạm object ở một phần, chưa phủ kín như trường hợp Fit, nhưng như vậy đã đủ để được xem là Hit.

Có thể hiểu đơn giản: Structuring Element chỉ cần “đụng” vào object.

So với Fit, Hit là điều kiện nhẹ hơn nhiều. Nó không yêu cầu phủ trọn object, mà chỉ cần có sự tiếp xúc. Vì vậy, Hit thường gắn với ý tưởng **mở rộng ảnh hưởng ra vùng lân cận** quanh object.

### Neither

Trường hợp **C: Neither** là khi không có ô active nào của Structuring Element chạm vào object. Khi đó, Structuring Element hoàn toàn nằm trên background nên không thỏa cả Fit lẫn Hit.

Ba ví dụ A, B, C trong hình vì thế tạo thành một cách nhìn rất trực quan:

- **Fit**: phủ trọn phần cần kiểm tra.
- **Hit**: chỉ cần chạm vào phần cần kiểm tra.
- **Neither**: không hề chạm.

Từ trực giác này, ta có thể hiểu hai phép Morphology cơ bản ở bước tiếp theo.

- **Erosion** dựa trên ý tưởng **Fit**: chỉ giữ lại những vị trí mà Structuring Element nằm gọn trong object.
- **Dilation** dựa trên ý tưởng **Hit**: chỉ cần Structuring Element chạm object thì vị trí đó đã có thể được bật lên.

Vì vậy, nếu nhớ tốt bốn ý **shape, origin, fit, hit**, thì việc hiểu Erosion và Dilation sẽ trở nên tự nhiên hơn rất nhiều. Shape quyết định ta đang tìm kiểu cấu trúc nào, origin xác định pixel tham chiếu, fit là điều kiện chặt, còn hit là điều kiện lỏng.

## Erosion and Dilation

Sau khi đã có **structuring element** và hiểu các khái niệm **origin**, **fit** và **hit**, ta có thể đi vào hai phép toán hình thái cơ bản nhất là **erosion** và **dilation**. Cả hai phép toán đều hoạt động theo cùng một ý tưởng: ta cho **structuring element** trượt qua từng vị trí trên ảnh nhị phân, rồi quyết định pixel output tại **origin** sẽ được giữ hay bật lên dựa trên một điều kiện hình học.

### Erosion

Với **erosion**, pixel tại vị trí đang xét chỉ được giữ lại nếu **structuring element fit lên object**. Nói cách khác, toàn bộ các ô đang được kích hoạt trong structuring element phải nằm trọn trên foreground.

Điều này giải thích phần minh họa bên trái của hình. Ở các vị trí có dấu **✓**, kernel vẫn nằm gọn trong object nên pixel output được giữ. Ngược lại, ở các vị trí có dấu **×**, một phần kernel đã chạm ra ngoài object nên pixel đó bị loại bỏ. Vì các điểm biên thường là nơi kernel khó fit hoàn toàn nhất, chúng sẽ biến mất trước.

Kết quả là **erosion làm foreground co lại**. Object trở nên mảnh hơn, các phần lồi nhỏ bị bào mòn, và những nét mỏng hoặc cầu nối hẹp có thể bị đứt nếu kernel đủ lớn.

Điều này cũng được thể hiện rất rõ ở ví dụ chữ **A** phía dưới. Với kernel `3×3`, chữ bị mỏng đi nhưng vẫn còn giữ được hình dạng chính. Khi tăng lên kernel `5×5`, phần foreground bị co mạnh hơn nhiều, các nét mảnh bị ăn mòn đáng kể và một số phần nhỏ gần như biến mất.

### Dilation

Ngược lại, với **dilation**, pixel tại vị trí đang xét sẽ được bật lên nếu **structuring element hit object**. Điều kiện này lỏng hơn erosion: chỉ cần có ít nhất một phần foreground của object chạm vào vùng kích hoạt của kernel thì output tại origin sẽ trở thành foreground.

Vì vậy ở phần minh họa bên phải, có nhiều vị trí được chấp nhận hơn. Chỉ cần kernel chạm vào object là vị trí đó có thể được tô vào output. Kết quả sau cùng là vùng foreground lan rộng ra xung quanh object ban đầu.

Do đó, **dilation làm foreground nở ra**. Các nét trở nên dày hơn, các khe hẹp có thể được lấp lại, và những đoạn gần nhau có thể dính vào nhau nếu độ giãn đủ lớn.

Ví dụ chữ **A** cho thấy điều này rất trực quan. Với kernel `3×3`, chữ đậm hơn và các nét dày hơn. Với kernel `5×5`, hiệu ứng còn mạnh hơn nữa: foreground được mở rộng rõ rệt và toàn bộ ký tự trở nên “béo” hơn so với ban đầu.

### Vai trò của kích thước kernel

Một điểm rất quan trọng trong hình là cùng một phép toán nhưng **kernel lớn hơn sẽ tạo hiệu ứng mạnh hơn**.

- Với **erosion**, kernel càng lớn thì điều kiện fit càng khó thỏa, nên object bị co càng mạnh.
- Với **dilation**, kernel càng lớn thì vùng có thể hit object càng rộng, nên object nở ra càng nhiều.

Vì vậy, kích thước của structuring element không chỉ là chi tiết cài đặt, mà nó quyết định trực tiếp mức độ biến đổi của hình dạng.

### Ý nghĩa trực giác

Có thể nhớ ngắn gọn như sau:

- **Erosion**: giữ lại những nơi kernel **fit hoàn toàn** vào object → object **co lại**.
- **Dilation**: bật lên những nơi kernel **chạm được** object → object **nở ra**.

Hai phép toán này là nền tảng cho các phép phức hợp hơn như **opening**, **closing**, và về sau sẽ rất quan trọng khi ta muốn tách các cấu trúc dài theo phương ngang hoặc phương dọc.

## **Opening & Closing**

Erosion và Dilation thường không được dùng riêng lẻ. Mỗi phép đều giải quyết được một loại vấn đề nhưng đồng thời cũng tạo ra một tác động phụ.

- **Erosion** có thể loại những foreground detail nhỏ, nhưng cũng làm object co lại.
- **Dilation** có thể lấp những gap nhỏ, nhưng cũng làm object nở ra.

Vì vậy, một ý tưởng tự nhiên là **ghép hai phép theo một thứ tự nhất định**, để tận dụng ưu điểm của phép đầu tiên rồi dùng phép thứ hai phục hồi lại hình dạng tốt hơn. Hai tổ hợp phổ biến nhất là **Opening** và **Closing**.

### Opening

**Opening** thực hiện Erosion trước, sau đó Dilation bằng cùng một Structuring Element:

$$

A \circ B = (A \ominus B) \oplus B

$$

Ở bước đầu, Erosion kiểm tra điều kiện Fit. Những foreground structure quá nhỏ hoặc quá mảnh để chứa Structuring Element sẽ bị loại. Các object lớn hơn vẫn tồn tại nhưng bị co lại.

Sau đó Dilation được áp dụng lên phần foreground còn lại. Những object sống sót sau Erosion sẽ nở trở lại và tiến gần hơn về kích thước ban đầu.

**[CHÈN HÌNH: Original → Erosion → Dilation → Opening Result]**

*Hình. Opening loại những foreground structure nhỏ ở bước Erosion, sau đó Dilation phục hồi lại phần object còn tồn tại.*

Điểm quan trọng là Dilation **không thể khôi phục một foreground structure đã bị Erosion xóa hoàn toàn**. Nó chỉ có thể mở rộng những pixel foreground vẫn còn tồn tại.

Vì vậy, Opening thường tạo ra hiệu ứng:

- loại các foreground detail nhỏ
- loại các chấm noise nhỏ
- phá những connection rất mảnh
- giữ lại tương đối tốt các object lớn hơn Structuring Element

Có thể nhớ trực giác:

> **Opening ưu tiên giữ những foreground structure đủ lớn để sống sót qua Erosion.**

---

### Closing

**Closing** đảo ngược thứ tự:

$$

A \bullet B = (A \oplus B) \ominus B

$$

Dilation được thực hiện trước, làm foreground lan rộng ra xung quanh. Nếu hai vùng foreground chỉ cách nhau bởi một gap nhỏ, chúng có thể mở rộng cho đến khi chạm nhau và tạo thành một connection mới.

Sau đó Erosion thu foreground lại. Object trở về gần kích thước ban đầu, nhưng connection vừa được tạo ra có thể vẫn được giữ lại.

**[CHÈN HÌNH: Original → Dilation → Erosion → Closing Result]**

*Hình. Closing mở rộng foreground để lấp các gap nhỏ, sau đó Erosion thu object trở lại gần kích thước ban đầu.*

Vì vậy, Closing thường hữu ích khi foreground có:

- break nhỏ
- gap hẹp
- hole nhỏ
- hai vùng gần nhau cần được nối lại

Có thể nhớ trực giác:

> **Closing ưu tiên đóng những khoảng background nhỏ nằm bên trong hoặc giữa các foreground structure.**

---

Điểm khác biệt cốt lõi nằm ở **thứ tự**:

# $$  \text{Opening}

\text{Erosion}

\rightarrow

\text{Dilation}

$$

# $$  \text{Closing}

\text{Dilation}

\rightarrow

\text{Erosion}

$$

Opening bắt đầu bằng việc loại foreground nhỏ. Closing bắt đầu bằng việc lấp background gap nhỏ. Vì thứ tự khác nhau, hai phép tạo ra hai loại hiệu ứng hình học khác nhau dù đều sử dụng cùng Erosion và Dilation.

## Directional Morphology for Grid Extraction

Đến đây, các phép morphology đã được hiểu ở mức tổng quát. Bước tiếp theo là khai thác một tính chất quan trọng của Structuring Element:

> **Shape của Structuring Element có thể được thiết kế để ưu tiên một hướng cụ thể.**

Nếu dùng một Structuring Element dài theo phương ngang, các foreground structure cũng kéo dài theo phương ngang sẽ có nhiều khả năng sống sót qua Erosion hơn. Những cấu trúc nhỏ, ngắn hoặc không liên tục theo hướng ngang thường bị loại sớm hơn.

Sau đó Dilation mở rộng lại những cấu trúc còn tồn tại.

Về trực giác, đây là một dạng **directional Opening**:

# $$  \text{Horizontal Opening}

\text{Erosion with Horizontal SE}

\rightarrow

\text{Dilation with Horizontal SE}

$$

Tương tự:

# $$  \text{Vertical Opening}

\text{Erosion with Vertical SE}

\rightarrow

\text{Dilation with Vertical SE}

$$

Khi áp dụng hai hướng này lên cùng một binary image, ta thu được hai mask riêng:

- **Horizontal Mask** giữ những cấu trúc dài theo phương ngang
- **Vertical Mask** giữ những cấu trúc dài theo phương dọc

Đây là lúc morphology bắt đầu quay lại đúng domain của bài toán table grid. Trong ảnh bảng, text và table lines đều là foreground, nhưng table grid có một prior hình học rất mạnh: nó chủ yếu được tạo bởi các đường ngang và đường dọc dài.

Vì vậy, thay vì cố nhận diện từng ký tự để loại text, ta dùng chính orientation của Structuring Element để giữ lại hai nhóm cấu trúc cần thiết.

**[CHÈN HÌNH: Binary Image ở giữa. Nhánh trên dùng Horizontal SE → Erosion → Dilation → Horizontal Mask. Nhánh dưới dùng Vertical SE → Erosion → Dilation → Vertical Mask.]**

*Hình. Directional morphology tách riêng các cấu trúc ngang và dọc từ cùng một binary image.*

Sau khi có hai mask, bước tiếp theo là ghép chúng lại:

$$

G = H \cup V

$$

Trong đó:

- $H$ là horizontal line mask
- $V$ là vertical line mask
- $G$ là grid mask

Có thể hiểu đây đơn giản là phép OR giữa hai mask.

Những pixel thuộc horizontal lines hoặc vertical lines đều được giữ lại trong $G$, nhờ vậy cấu trúc grid bắt đầu xuất hiện trở lại.

**[CHÈN HÌNH: Horizontal Mask + Vertical Mask → OR → Grid Mask]**

*Hình. Ghép hai directional masks giúp phục hồi cấu trúc grid của bảng.*

Trong ảnh thật, grid có thể vẫn còn một số khoảng hở nhỏ do thresholding, scan quality hoặc line bị đứt nhẹ. Khi cần, có thể dùng một **Dilation nhẹ** sau khi combine để tăng connectivity:

# $$  G'

\operatorname{dilate}(H \cup V)

$$

Mục tiêu không phải làm line càng dày càng tốt, mà chỉ để:

- nối các gap nhỏ
- làm các intersection chắc hơn
- giúp grid trở thành một cấu trúc liên tục hơn

Kết quả cuối cùng vẫn là một **pixel mask**, không phải danh sách line segments. Đây là điểm rất phù hợp cho bước tiếp theo, vì ta có thể trực tiếp tìm table region, contour, intersection hoặc reconstruct cell từ cấu trúc mask này.

## Find Contour

## Why contours? From pixels to object geometry

Sau thresholding và morphology, ta thu được một binary mask: pixel trắng thuộc foreground, pixel đen thuộc background. Khi các đường ngang và dọc được ghép lại, chúng tạo thành một vùng foreground đại diện cho bảng.

Tuy nhiên, binary mask mới chỉ biểu diễn object ở mức pixel. Muốn xác định bảng nằm ở đâu, rộng bao nhiêu và cao bao nhiêu, hệ thống cần một biểu diễn hình học thuận tiện hơn.

Contour là đường bao của object, được biểu diễn như một chuỗi điểm có thứ tự chạy quanh biên. Nhờ đó, hệ thống có thể chuyển từ một vùng pixel sang một đối tượng hình học có vị trí, kích thước và diện tích rõ ràng.

**[CHÈN HÌNH: Joined Line Mask → External Boundary Pixels → Full Ordered Boundary → Candidate Bounding Box]**

*Hình. Từ line mask, hệ thống lần theo biên ngoài để tạo contour, rồi dùng contour đó để xác định bounding box của bảng.*

Trong hình:

1. **Joined line mask:** các đường ngang và dọc đã được ghép thành một vùng foreground liên thông.
2. **External boundary pixels:** các pixel nằm trên biên ngoài của vùng này được nhận diện.
3. **Full ordered boundary:** các điểm biên được sắp theo thứ tự chạy liên tục quanh object để tạo thành contour hoàn chỉnh.
4. **Candidate bounding box:** từ contour, hệ thống lấy hình chữ nhật bao ngoài để xác định vị trí và kích thước của bảng trên trang.

Trong bước định vị bảng, hệ thống chủ yếu quan tâm đến đường bao ngoài của toàn bộ bảng. Các đường kẻ và ô bên trong vẫn được giữ lại trong line mask để dùng cho bước khôi phục hàng, cột ở phía sau.

### Takeaway

Binary mask cho biết object nằm ở những pixel nào. Contour tổ chức biên của object thành một dạng hình học, từ đó hệ thống xác định được vị trí và bounding box của bảng.

## Region, Border & Contour

Để hiểu contour rõ hơn, trước hết cần phân biệt ba khái niệm rất gần nhau là **Region**, **Border** và **Contour**.

**Region** là toàn bộ vùng foreground thuộc về object. Nếu một object được tô kín trong binary image, tất cả các pixel bên trong nó đều thuộc region.

**Border** hay **Boundary** chỉ là các pixel nằm ở rìa của object, tức những pixel foreground tiếp xúc với background. Nó mô tả phần biên ngoài của region.

**Contour** tiến thêm một bước nữa. Thay vì chỉ biết những pixel nào nằm trên boundary, contour biểu diễn boundary thành một **chuỗi các điểm có thứ tự** chạy liên tục quanh object.

**[CHÈN HÌNH: cùng một object được minh họa lần lượt dưới dạng Region → Border → Ordered Contour]**

*Hình. Region gồm toàn bộ object, Border chỉ giữ các pixel ở rìa, còn Contour tổ chức boundary thành một chuỗi điểm có thứ tự.*

Điểm dễ nhầm nhất nằm giữa **Border** và **Contour**.

Border chỉ trả lời:

> "Những pixel nào nằm trên biên?"

Trong khi Contour còn trả lời:

> "Các điểm trên biên được nối với nhau theo thứ tự nào?"

Chính thông tin về thứ tự này làm contour trở thành một representation hình học thuận tiện hơn. Từ contour, hệ thống có thể lần theo toàn bộ đường bao, tính perimeter, tạo bounding box hoặc thực hiện các phép đo hình dạng khác.

## How Contours Are Found: Raster Scan + Border Following

Sau khi đã hiểu contour là một chuỗi điểm có thứ tự chạy quanh boundary, câu hỏi tiếp theo là:

> **Thuật toán bắt đầu contour ở đâu, và làm thế nào để lần theo toàn bộ đường biên?**

Có thể hiểu quá trình này gồm hai nhiệm vụ nối tiếp nhau:

- **Raster Scan** tìm vị trí bắt đầu của một contour mới.
- **Border Following** lần theo boundary từ vị trí đó cho đến khi contour khép kín.

**[CHÈN HÌNH: Raster scan tìm boundary start → 8-neighborhood → ordered contour → close & resume]**

*Hình. Raster scan tìm điểm bắt đầu của contour, sau đó Border Following lần theo các boundary pixels cho đến khi contour khép kín.*

### Raster Scan: tìm boundary start

Đầu tiên, thuật toán quét ảnh theo kiểu **Raster Scan**, tức đi từ trái sang phải trên từng hàng rồi tiếp tục từ trên xuống dưới. Mục tiêu của bước này chưa phải là lần theo contour, mà chỉ là tìm một pixel có thể bắt đầu một border mới.

Với một outer boundary đơn giản, khi quá trình quét đi từ background sang foreground:

$0 \rightarrow 1$

pixel foreground vừa gặp có thể là **boundary start**.

Trong hình, raster scan tiếp tục cho đến khi gặp điểm $p_0$. Từ thời điểm đó, việc quét toàn ảnh tạm dừng và thuật toán chuyển sang nhiệm vụ khác: lần theo chính boundary vừa phát hiện.

### Border Following: tìm boundary pixel tiếp theo

Khi đã có starting point, thuật toán không còn hỏi:

> "Có contour mới ở đây không?"

mà chuyển sang:

> **"Boundary pixel tiếp theo nằm ở đâu?"**

Tại mỗi current pixel, thuật toán quan sát các pixel lân cận, thường dùng **8-neighborhood**, tức tám vị trí nằm ngang, dọc và chéo xung quanh pixel hiện tại. Từ neighborhood này, thuật toán chọn boundary pixel phù hợp tiếp theo rồi di chuyển tới đó.

Quá trình có thể hình dung như:

**current boundary pixel → search neighborhood → next boundary pixel → continue tracing**

Điểm quan trọng là việc kiểm tra neighborhood không nên hiểu là luôn bắt đầu từ cùng một hướng cố định tại mọi pixel. Hướng tìm kiếm thường phụ thuộc vào boundary step trước đó để contour được lần theo liên tục quanh object.

Trong hình, các điểm $p_0, p_1, \ldots$ minh họa **một ví dụ về thứ tự contour được trả về**. Chiều traversal có thể khác ở object hoặc implementation khác, nhưng các điểm vẫn mô tả cùng một boundary hình học.

### Khi nào contour hoàn thành?

Border Following tiếp tục cho đến khi thuật toán quay trở lại **trạng thái boundary ban đầu**, nghĩa là contour đã được lần theo trọn một vòng và được xác định là closed. Các điểm đã đi qua được lưu theo thứ tự và tạo thành contour.

Sau đó thuật toán quay lại vị trí raster scan đang dở và tiếp tục quét ảnh để tìm contour tiếp theo.

## Outer, Hole & Contour Hierarchy

Một binary image có thể chứa nhiều contour không chỉ vì có nhiều object tách biệt. **Ngay cả một object duy nhất cũng có thể tạo ra nhiều contour nếu bên trong nó có vùng rỗng.**

Ví dụ đơn giản nhất là một object giống chiếc vòng. Ta có thể quan sát hai boundary khác nhau:

- **Outer contour**: đường bao chạy quanh phía ngoài của object.
- **Hole contour** hay **inner contour**: đường bao chạy quanh vùng background bị object bao kín bên trong.

**[CHÈN HÌNH: một object dạng vòng với Outer Contour màu xanh và Hole Contour màu cam]**

*Hình. Một object có thể tạo ra outer contour ở bên ngoài và hole contour bao quanh vùng background bên trong.*

Điểm quan trọng là **hole không phải foreground object mới**. Nó vẫn là background, nhưng vì vùng background này bị foreground bao kín hoàn toàn nên boundary của nó cũng có thể được biểu diễn thành một contour.

Khi các contour nằm bên trong nhau, ta bắt đầu có một **Contour Hierarchy**, tức cấu trúc mô tả contour nào đang chứa contour nào.

Ba quan hệ cơ bản là:

- **Parent**: contour nằm bên ngoài và chứa contour khác.
- **Child**: contour nằm bên trong một contour khác.
- **Sibling**: các contour nằm cùng cấp và có cùng parent.

Ví dụ, nếu một object lớn chứa một hole, thì outer contour có thể được xem là **parent**, còn hole contour là **child** của nó.

Nếu bên trong hole lại xuất hiện một foreground object khác, object đó lại có contour riêng và hierarchy có thể tiếp tục sâu thêm một cấp.

**[CHÈN HÌNH: Outer contour → Hole contour → Inner object, minh họa parent / child / sibling bằng cây hierarchy nhỏ bên cạnh]**

*Hình. Các contour lồng nhau tạo thành quan hệ phân cấp giữa parent, child và sibling.*

Hierarchy quan trọng vì một ảnh có thể chứa nhiều contour nhưng ta không phải lúc nào cũng muốn xử lý chúng như những object độc lập. Quan hệ bao chứa cho biết contour nào thuộc cùng một cấu trúc lớn hơn.

Trong các thuật toán border following, hierarchy có thể được xác định ngay trong quá trình quét. Khi một border mới được phát hiện, thuật toán không chỉ trace contour đó mà còn có thể xác định contour nào đang bao quanh nó để suy ra quan hệ cha–con.

## Using Contours in OpenCV: Retrieval, Approximation & Table Localization

Sau khi đã hiểu contour được tìm như thế nào và hierarchy được hình thành ra sao, bước tiếp theo là xem OpenCV cho phép ta **chọn contour nào cần lấy**, **lưu contour chi tiết đến mức nào**, rồi dùng contour đó để xác định vùng bảng.

Trong OpenCV, hàm cơ bản là:

```python
contours,hierarchy=cv2.findContours(binary,mode,method)

```

Trong đó:

- `mode` quyết định **retrieval strategy**, tức muốn lấy contour nào và có giữ hierarchy hay không
- `method` quyết định **contour approximation**, tức mỗi contour sẽ được lưu bằng nhiều hay ít điểm

### Retrieval Mode: lấy contour nào?

Không phải lúc nào ta cũng cần tất cả contour trong ảnh.

Nếu chỉ cần những contour ngoài cùng, có thể dùng:

```
cv2.RETR_EXTERNAL

```

Mode này chỉ giữ **outermost contours** và bỏ qua các contour nằm sâu bên trong. Với bài toán định vị toàn bộ bảng, đây thường là lựa chọn phù hợp vì ta quan tâm đến boundary ngoài của vùng grid, không phải từng cell bên trong.

Nếu cần giữ toàn bộ cấu trúc lồng nhau giữa outer contour, hole contour và các contour bên trong, có thể dùng:

```
cv2.RETR_TREE

```

Khi đó hierarchy được lưu đầy đủ theo quan hệ parent–child. Điều này hữu ích hơn nếu mục tiêu phía sau cần khai thác cấu trúc bên trong thay vì chỉ xác định vùng ngoài cùng.

Có thể nhớ ngắn gọn:

> **Retrieval mode trả lời: “Mình muốn lấy những contour nào?”**

---

### Contour Approximation: cần giữ bao nhiêu điểm?

Sau khi đã tìm được boundary, ta chưa chắc cần lưu toàn bộ pixel nằm trên đường biên.

Ví dụ, một cạnh bảng có thể dài hàng trăm pixel nhưng vẫn chỉ là một đoạn thẳng. Việc lưu từng pixel trên cạnh đó là dư thừa nếu mục tiêu chỉ là mô tả shape.

Hai lựa chọn thường gặp là:

```
cv2.CHAIN_APPROX_NONE

```

gần như giữ toàn bộ boundary points,

và:

```
cv2.CHAIN_APPROX_SIMPLE

```

loại bớt các điểm dư trên những đoạn thẳng và chỉ giữ các điểm cần thiết để mô tả hình dạng.

Có thể nhớ:

> **Retrieval = lấy contour nào?**
>
> **Approximation = contour đó cần lưu bao nhiêu điểm?**

---

### From Grid Mask to Table Localization

Quay lại pipeline hiện tại, sau directional morphology ta đã có **grid mask**, tức mask chứa chủ yếu các đường ngang và dọc của bảng.

Lúc này có thể gọi:

```
contours,_=cv2.findContours(joined,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE
)

```

`RETR_EXTERNAL` phù hợp vì mục tiêu là lấy **outer contour của toàn bộ vùng bảng**. Các cell bên trong có thể tạo ra nhiều vùng kín, nhưng ở bước localization ta chưa cần các contour đó.

Sau khi có contour, ta chuyển nó thành bounding box bằng:

```
x,y,w,h=cv2.boundingRect(contour)

```

Bounding box cho biết:

- vị trí góc trên-trái `(x, y)`
- chiều rộng `w`
- chiều cao `h`

Từ đó, mỗi contour ngoài cùng có thể trở thành một **table candidate region** trên trang.

**[CHÈN HÌNH: Grid Mask → RETR_EXTERNAL → Outer Contour → CHAIN_APPROX_SIMPLE → Bounding Box]**

*Hình. OpenCV dùng retrieval mode để chọn contour cần lấy, approximation để giảm số điểm dư, rồi chuyển outer contour thành bounding box của bảng.*

# 5. Grid & Logical Cell Reconstruction

## Recover Global Grid Edges

Sau Morphological Line Extraction, ta đã có **vertical mask** và **horizontal mask**. Hai mask này vẫn là biểu diễn ở mức pixel, trong khi bước reconstruct grid cần một tập tọa độ rõ ràng hơn cho các ranh giới cột và hàng:

$x\_{\text{edges}}$ và $y\_{\text{edges}}$

Ý tưởng chính là dùng **projection** để biến các đường trong mask thành response trên một trục.

Với vertical mask, tại mỗi vị trí $x$, ta đếm số foreground pixels theo chiều cao:

$P_v(x) = \sum_y \mathbf{1}[V(y,x) > 0]$

Nếu tại một tọa độ $x$ tồn tại một vertical line đủ dài, response tại đó sẽ lớn. Những vùng vượt threshold trở thành candidate cho **column boundaries**.

Horizontal mask được xử lý tương tự:

$P_h(y) = \sum_x \mathbf{1}[H(y,x) > 0]$

Một horizontal line đủ dài tạo response lớn tại vị trí $y$, từ đó ta thu được candidate cho **row boundaries**.

Nhìn vào hình, các peak của vertical projection thẳng hàng với $x_0, x_1, \ldots$, còn các peak của horizontal projection tương ứng với $y_0, y_1, \ldots$.

Điểm quan trọng là một grid line thực tế không nhất thiết chỉ tạo ra một pixel response. Line có thể dày vài pixel hoặc bị ngắt nhẹ, nên các candidate gần nhau cần được gom thành **line runs** trước khi chuyển thành edge.

Với một run mỏng thông thường, hệ thống lấy vị trí giữa làm edge đại diện. Nhưng nếu response tạo thành một band rộng bất thường, implementation giữ cả hai phía của band vì chúng có thể tương ứng với hai boundary khác nhau.

Các response bị đứt bởi một gap nhỏ vẫn có thể được xem là cùng một run. Ngược lại, những edge candidate sau xử lý nhưng nằm quá gần nhau sẽ được deduplicate để tránh sinh ra những hàng hoặc cột rất hẹp không có thật.

Hình cũng cho thấy một nguồn thông tin thứ hai là **table bounding box** từ bước contour trước. Projection chủ yếu khôi phục cấu trúc grid từ line masks, nhưng outer border đôi khi yếu hoặc bị mất. Khi projection không tìm được boundary đủ gần mép bảng, bounding box có thể được dùng để bổ sung outer edge.

Vì vậy, bước này kết hợp hai nguồn evidence:

> **Line masks cho biết các separator nằm ở đâu, còn table bounding box giúp đảm bảo grid có đầy đủ outer boundaries.**

Kết quả cuối cùng là hai dãy tọa độ tăng dần:

$x_0 < x_1 < \cdots < x_n$

$y_0 < y_1 < \cdots < y_m$

Chúng tạo thành **global coordinate system** của bảng. Bước tiếp theo sẽ dùng từng cặp edge liên tiếp để dựng các **atomic cells**.

## From Grid Edges to Atomic Cells

Sau bước Recover Global Grid Edges, ta đã có hai tập tọa độ:

$x\_{\text{edges}} = [x_0, x_1, \ldots, x_n]$

$y\_{\text{edges}} = [y_0, y_1, \ldots, y_m]$

Ở giai đoạn này, các global edges được xem như những **đường tọa độ kéo dài xuyên qua toàn bộ table region**. Khi các đường dọc và ngang giao nhau, chúng tạo thành một Cartesian grid chung cho toàn bảng.

Mỗi cặp $x\_{\text{edges}}$ liên tiếp xác định giới hạn theo chiều ngang, còn mỗi cặp $y\_{\text{edges}}$ liên tiếp xác định giới hạn theo chiều dọc. Vì vậy, một atomic cell tại hàng $r$, cột $c$ được định nghĩa bởi:

$A\_{r,c} = [x_c, x\_{c+1}) \times [y_r, y\_{r+1})$

Trong hình, $Cell\ (0,1)$ nằm giữa:

$x_1 \rightarrow x_2$

và:

$y_0 \rightarrow y_1$

nên vùng của cell này là:

$[x_1, x_2) \times [y_0, y_1)$

Dấu ngoặc phải mở thể hiện cách biểu diễn **half-open interval**. Edge bên phải hoặc bên dưới sẽ thuộc về cell kế tiếp, nhờ đó hai atomic cells liền nhau không chồng lấn về mặt tọa độ.

Nếu có $n+1$ vertical edges và $m+1$ horizontal edges, số atomic cells được tạo ra là:

$m \times n$

Ví dụ trong hình:

$x\_{\text{edges}} = [x_0, x_1, x_2, x_3]$

và:

$y\_{\text{edges}} = [y_0, y_1, y_2]$

tạo ra một atomic grid gồm:

$2 \times 3 = 6$

cells.

Điểm quan trọng là **atomic grid mới chỉ là một phép chia hình học dựa trên global coordinates**. Việc một $y\_{\text{edge}}$ hoặc $x\_{\text{edge}}$ tồn tại ở mức toàn bảng không có nghĩa separator đó thực sự xuất hiện ở mọi đoạn cục bộ.

Ví dụ, $y_1$ có thể được phát hiện vì horizontal line tồn tại trên phần lớn chiều rộng bảng. Nhưng tại một cột cụ thể, separator này có thể bị thiếu vì cell ở đó thực tế span qua hai hàng.

Do đó:

> **Atomic cell chưa phải logical cell cuối cùng.**

Atomic cells chỉ là những đơn vị cơ sở nhỏ nhất để bước tiếp theo kiểm tra separator cục bộ. Nếu separator giữa hai atomic cells thực sự không tồn tại, các cell đó có thể được gom lại thành một logical region lớn hơn.

## Local Separator Evidence

Atomic grid ở bước trước được tạo từ các global $x\_{\text{edges}}$ và $y\_{\text{edges}}$. Tuy nhiên, một global edge chỉ cho biết **tọa độ candidate separator ở mức toàn bảng**, chứ chưa chứng minh rằng separator đó thực sự tồn tại tại mọi column.

Trong hình, đường dashed màu xanh tại $y_k$ chính là **global candidate coordinate**. Nó chạy xuyên qua toàn bộ bảng để tạo hệ tọa độ chung, nhưng các đoạn separator thực sự quan sát được được biểu diễn bằng những line segment đậm nằm trên đường này.

Ta có thể thấy:

- column $c-1$: separator xuất hiện rõ
- column $c$: separator xuất hiện rõ
- column $c+1$: separator gần như bị thiếu
- column $c+2$: separator xuất hiện rõ
- column $c+3$: separator xuất hiện rõ

Như vậy, cùng một global $y_k$ vẫn có thể hợp lệ ở mức toàn bảng dù separator bị thiếu tại riêng một column.

Để kiểm tra trường hợp này, implementation quay lại **horizontal mask** và xét separator cục bộ trong từng column.

Với column $c+1$, hệ thống không chỉ nhìn đúng hàng $y_k$, mà kiểm tra một band cao 5 pixel:

$y_k-2,\ldots,y_k+2$

Khoảng kiểm tra theo chiều ngang cũng được thu hẹp lại để tránh ảnh hưởng từ vertical borders:

$[x\_{c+1}+3,\\;x\_{c+2}-3)$

Tại mỗi vị trí $x$ trong khoảng này, chỉ cần có ít nhất một foreground pixel xuất hiện trong band thì vị trí đó được xem là có **separator evidence**.

Vì vậy coverage được tính theo số **horizontal positions có evidence**, không phải tổng số foreground pixels:

$\text{coverage} = \frac{\text{horizontal positions with line evidence}}{\text{usable segment width}}$

Trong phần zoom của hình, chỉ có **1 vị trí có evidence trên 13 vị trí usable**, nên:

$\text{coverage} = \frac{1}{13} \approx 8\\%$

Đây là coverage rất thấp.

Ngược lại, ở các column khác, horizontal separator xuất hiện trên phần lớn chiều rộng nên coverage cao và hai atomic cells được giữ tách biệt.

Implementation hiện tại dùng ngưỡng:

$\text{coverage} < 0.20$

Nếu coverage thấp hơn ngưỡng này, separator được xem là không tồn tại đủ mạnh tại local segment đó.

Khi đó hai atomic cells kề nhau theo chiều dọc:

$A\_{k,c+1}$

và

$A\_{k+1,c+1}$

được **đánh dấu để union**, tức tạo một vertical merge relation.

Điểm quan trọng là hai tầng evidence phục vụ hai mục tiêu khác nhau:

> **Global edge đề xuất separator nằm ở đâu. Local coverage quyết định separator đó có thực sự tách hai atomic cells tại column hiện tại hay không.**

Trong implementation hiện tại, cơ chế này chỉ dùng để suy luận:

> **Missing horizontal separator → vertical merge**

Horizontal merge chưa được suy ra từ vertical coverage. Phần đó được xử lý riêng ở bước tiếp theo bằng M2 table grammar.

## From Merge Relations to Logical Regions

Sau bước Local Separator Evidence, hệ thống đã có các **merge relations** giữa những atomic cells có khả năng thuộc cùng một logical cell. Tuy nhiên, một merged cell có thể bao gồm nhiều atomic cells được nối qua nhiều relation khác nhau, nên ta cần gom các quan hệ này lại trước khi tạo region cuối cùng.

Implementation hiện tại có hai nguồn merge relation:

- **Vertical merge** khi horizontal separator cục bộ có coverage thấp.
- **Horizontal merge** ở phần header của bảng M2, dựa trên header grammar sau khi M2 được nhận diện từ grid geometry.

### Group atomic cells with Union-Find

Ban đầu, mỗi atomic cell là một component riêng.

Mỗi merge relation nối hai atomic cells với nhau. **Union-Find** được dùng để gom các relation nối tiếp thành cùng một connected component.

Trong hình, ba nhóm $C_1$, $C_2$, $C_3$ được hình thành từ các merge relations:

- $C_1$ gồm hai atomic cells nằm ngang cạnh nhau.
- $C_2$ gồm hai atomic cells nằm dọc.
- $C_3$ cũng gồm hai atomic cells nằm dọc.

Có thể hiểu đơn giản:

> **Merge relations xác định các kết nối cục bộ. Union-Find gom toàn bộ các kết nối đó thành candidate logical regions.**

### Rectangle Validation

Một Union-Find component chưa tự động trở thành logical cell.

Representation cuối cùng giả định mỗi `CellRegion` phải là **một hình chữ nhật đầy đủ trên atomic grid**. Vì vậy, hệ thống kiểm tra bounding rows và columns của component rồi xác nhận rằng tất cả atomic positions bên trong rectangle đó đều thực sự thuộc component.

Trong hình:

$C_1:\ \text{rows }[0,1),\ \text{cols }[1,3)$

nên:

$1 \times 2$

Tương tự:

$C_2:\ \text{rows }[1,3),\ \text{cols }[1,2)$

và:

$C_3:\ \text{rows }[2,4),\ \text{cols }[3,4)$

đều tạo thành các rectangle hợp lệ.

### From Components to `CellRegion`

Những component vượt qua rectangle validation được chuyển thành logical `CellRegion`. Ví dụ:

$C_1 = \text{CellRegion}(0,1,1,3)$

nghĩa là region này phủ:

- row $0$
- columns $1,2$
- $\text{rowspan} = 1$
- $\text{colspan} = 2$

`row1` và `col1` là **exclusive**, nên rectangle được xác định trực tiếp từ:

$[y\_{\text{row0}}, y\_{\text{row1}}) \times [x\_{\text{col0}}, x\_{\text{col1}})$

Các atomic cells không tham gia merge vẫn được giữ lại dưới dạng **singleton $1 \times 1$ `CellRegion`**. Trong hình, chúng chính là các ô màu xám ở panel cuối.

Điểm quan trọng là quá trình merge **không thay đổi $x\_{\text{edges}}$ hoặc $y\_{\text{edges}}$**. Atomic grid vẫn giữ nguyên. `CellRegion` chỉ bổ sung một lớp logic phía trên để cho biết nhiều atomic positions có thể thuộc cùng một cell.

## GridTable Representation

Sau khi đã suy ra các logical regions, bước cuối của phần Grid & Logical Cell Reconstruction là gom toàn bộ **geometry của bảng** vào một representation thống nhất là `GridTable`.

`GridTable` không chứa OCR text. Nó chỉ lưu cấu trúc hình học của bảng đã phát hiện, gồm:

- `bbox`: bounding box của toàn bảng
- `x_edges`: các vertical grid edges
- `y_edges`: các horizontal grid edges
- `regions`: các logical `CellRegion`

Trong hình, bounding box được biểu diễn bởi:

$\text{bbox} = (left,\ top,\ right,\ bottom)$

tương ứng với vùng half-open:

$[left, right) \times [top, bottom)$

Cách biểu diễn này khác với dạng `(x, y, w, h)`. Ở đây `right` và `bottom` là tọa độ biên ngoài, không phải width và height.

Các `x_edges` và `y_edges` tiếp tục giữ nguyên atomic coordinate system đã xây ở các bước trước:

$x\_{\text{edges}} = (x_0, x_1, x_2, x_3, x_4)$

$y\_{\text{edges}} = (y_0, y_1, y_2, y_3, y_4)$

Việc merge cell không xóa hay thay đổi những edge này. Thay vào đó, `regions` mô tả cách các atomic cells được nhóm thành logical cells.

Ví dụ region $C_1$ trong hình được biểu diễn bằng:

```python
CellRegion(
	row0=0,
	row1=1,
	col0=1,
	col1=3,
)

```

Region này phủ: $\text{rows }[0,1)$ và: $\text{cols }[1,3)$ nên:

$\text{rowspan} = 1$

$\text{colspan} = 2$

Về tọa độ pixel, $C_1$ tương ứng với rectangle: $[x_1, x_3) \times [y_0, y_1)$

Điểm quan trọng là `row1` và `col1` là **exclusive upper bounds**. Vì vậy `col1=3` nghĩa là region phủ columns `1` và `2`, chứ không bao gồm column `3`.

Tương tự, trong hình:

CellRegion(1, 3, 1, 2)

tạo region $C_2$ có kích thước $2 \times 1$, còn:

CellRegion(2, 4, 3, 4)

tạo region $C_3$ có kích thước $2 \times 1$.

Các atomic cells không tham gia merge vẫn được giữ trong `regions` dưới dạng **singleton $1 \times 1$ `CellRegion`**. Trong hình, đó là các ô màu xám.

Như vậy `GridTable` tạo ra hai tầng representation rất rõ:

> **`x_edges`, `y_edges` giữ geometry toàn cục của atomic grid, còn `CellRegion` mô tả các logical cells nằm trên grid đó.**

Điều này giúp các bước phía sau dễ dàng suy ra vị trí pixel, `rowspan`, `colspan` hoặc vùng crop của từng logical cell mà không cần reconstruct lại merge relations.

OCR text chưa nằm trong `GridTable`. Phần này chỉ giữ **geometric structure**. Nội dung nhận dạng sẽ được gắn vào cấu trúc bảng ở các bước tiếp theo.

# 6. Cell Recognition & Document Recovery

| Mục cuối Nội dung                                       |                                                                                                                                                                                 |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **6.1 Anchors & Merge Markers**                         | Chuyển các `CellRegion` thành cell matrix. `(row0, col0)` là anchor chứa text, các atomic positions còn lại dùng `[[H]]` hoặc `[[V]]`.                                          |
| **6.2 Logical Cell Recognition**                        | Từ mỗi logical region: pixel crop → bỏ margin border → split text bands theo chiều dọc → OCR từng band → nối bằng `<br>` → ghi kết quả tại anchor. Kết thúc bằng `TableResult`. |
| **6.3 Cross-Page Table Stitching**                      | Kiểm tra hai bảng có tương thích bằng số cột và normalized `x_edges`, bỏ 3 repeated header rows của trang 2 rồi nối cell matrices.                                              |
| **6.4 Bold Recovery & Extended Markdown Serialization** | Áp dụng M1/M2 bold grammar cùng stroke evidence, sau đó serialize text, `[[H]]`, `[[V]]`, `<br>`, escaped pipes và `**bold**` thành Markdown.                                   |

## 6.1. Anchors & Merge Markers

Sau khi đã có các logical `CellRegion`, bước tiếp theo là ánh xạ mỗi region trở lại **cell matrix** mà vẫn giữ được thông tin merged cell.

Mỗi `CellRegion` được xác định bởi:

$$

[row_0,row_1)\times[col_0,col_1)

$$

Trong hình, region:

$$

\text{CellRegion}(0,2,1,3)

$$

phủ hai hàng $r_0, r_1$ và hai cột $c_1, c_2$, nên tạo thành một logical region kích thước:

$$

2 \times 2

$$

Vị trí **top-left** của region được chọn làm **anchor**:

$$

(row_0,col_0)

$$

Anchor là vị trí đại diện cho logical cell và là nơi lưu nội dung của cell trong matrix.

Các atomic positions còn lại không chứa lại cùng một nội dung. Thay vào đó, chúng sử dụng continuation markers để biểu diễn cách logical cell trải rộng trên atomic grid.

- `[[H]]` biểu diễn **horizontal continuation**. Marker này liên kết với vị trí ở bên trái.
- `[[V]]` biểu diễn **vertical continuation**. Marker này liên kết với vị trí ở phía trên.

Trong ví dụ $2 \times 2$ trên hình, ô `[[H]]` ở top row nối ngược về anchor bên trái. Hai vị trí ở hàng dưới dùng `[[V]]`, cho biết chúng tiếp tục logical region từ hàng phía trên xuống.

Điểm quan trọng là bốn atomic positions này **không phải bốn cells độc lập**. Chúng chỉ là bốn vị trí trong cell matrix dùng để biểu diễn một logical `CellRegion` duy nhất.

Nhờ quy ước này, cell matrix vẫn giữ nguyên kích thước của atomic grid nhưng đồng thời bảo toàn được thông tin `rowspan` và `colspan` của merged cells.

Các marker `[[H]]` và `[[V]]` là **serialization convention của dataset**, không phải cú pháp Markdown chuẩn.

## 6.2. Logical Cell Recognition

Sau khi đã có `CellRegion` và anchor, hệ thống chuyển từ **logical geometry** sang **recognized cell content**.

Mỗi `CellRegion` xác định toàn bộ vùng của một logical cell thông qua các grid edges. Tọa độ crop được lấy từ `x_edges` và `y_edges`, sau đó thu vào khoảng `2 px` ở mỗi cạnh để giảm ảnh hưởng của table borders lên quá trình nhận dạng.

Trong hình, toàn bộ logical cell được crop một lần. Bên trong crop này, hệ thống tìm các **horizontal text bands**, tức những vùng chứa text ở các vị trí khác nhau theo chiều dọc.

Các bands được xử lý theo thứ tự từ trên xuống dưới:

1. `Item name`
2. `(additional info)`
3. `Unit price`

Mỗi band được OCR riêng. Sau đó, kết quả được nối lại bằng `<br>`:

`Item name<br>(additional info)<br>Unit price`

`<br>` được thêm sau OCR để giữ line breaks bên trong cùng một logical cell. Đây không phải ký tự do OCR tự sinh ra.

Joined text chỉ được ghi vào **anchor** của logical region. Các vị trí `[[H]]` và `[[V]]` trong cell matrix vẫn giữ nguyên, nên cấu trúc merged cell không bị mất khi thêm nội dung.

Song song với OCR, hệ thống còn tính một **stroke score** riêng từ logical-region crop. Score này không được lấy từ các OCR bands. Nó được lưu tại anchor, trong khi các marker positions không cần score. Evidence này sẽ được dùng ở bước Bold Recovery phía sau.

Sau khi tất cả logical regions được xử lý, hệ thống tạo:

`TableResult(grid=table, cells=cells, stroke_scores=stroke_scores)`

Trong đó:

- `grid` giữ geometry của bảng
- `cells` chứa recognized text tại anchors cùng `[[H]]`, `[[V]]`
- `stroke_scores` giữ visual evidence cho bước bold recovery

Ở bước này, thứ tự đọc chỉ được khôi phục **top-to-bottom trong từng logical cell**. Đây chưa phải một cơ chế reading order tổng quát cho toàn trang.

## 6.3. Cross-Page Table Stitching

Cross-page stitching chỉ được thử trong một trường hợp khá cụ thể: document có đúng **2 pages**, mỗi page phát hiện đúng **1 table**, hai bảng có cùng số cột, page 1 có ít nhất 3 hàng và page 2 có nhiều hơn 3 hàng.

Tiếp theo, hệ thống kiểm tra xem hai bảng có cùng cấu trúc cột hay không. Vì tọa độ pixel tuyệt đối giữa hai trang có thể khác nhau, các `x_edges` được normalize theo chiều rộng của từng bảng:

# $$  \tilde{x}\_i

\frac{x_i-x\_{\text{left}}}

{x\_{\text{right}}-x\_{\text{left}}}

$$

Hai bảng được xem là compatible khi độ lệch lớn nhất giữa các normalized edges tương ứng không vượt quá:

$$

\max_i

\left|

\tilde{x}^{(1)}\_i-\tilde{x}^{(2)}\_i

\right|

\le 0.025

$$

Nếu điều kiện này không đạt, hai bảng được giữ riêng.

Nếu compatible, implementation **giả định** rằng 3 hàng đầu của page 2 là phần header lặp lại và loại bỏ chúng trước khi nối nội dung.

Cell matrix được ghép theo:

`page1.cells + page2.cells[3:]`

`stroke_scores` cũng được nối tương tự **chỉ khi cả hai `TableResult` đều có scores**. Nếu một bên không có, stitched result sẽ giữ `stroke_scores=None`.

Phần geometry không được align hay transform giữa hai trang. Kết quả cuối vẫn giữ:

`grid = page1.grid`

Tức là `GridTable` của page 1 được dùng làm representative geometry, còn phần được stitch chủ yếu là cell contents và visual evidence.

Vì vậy, cơ chế này nên được hiểu là:

> **content-level stitching gated by compatible column structure**

chứ không phải geometric alignment giữa hai page images.

Trong implementation hiện tại, nếu bất kỳ eligibility check hoặc layout compatibility check nào thất bại, hệ thống không cố stitch mà giữ hai table results riêng biệt.

## 6.4 Bold Recovery

Sau OCR và optional cross-page stitching, cell matrix đã chứa recognized text, merge markers và `stroke_scores`. Bước này chỉ khôi phục **bold**. Các thuộc tính như italic, alignment, font size hay color chưa nằm trong phạm vi implementation hiện tại.

Với bảng **M1**, bold được xác định hoàn toàn từ table grammar. Row đầu tiên và row cuối cùng được bold:

$$

B\_{\text{M1}}=\\{0,n-1\\}

$$

Các body rows nằm giữa giữ normal.

Với bảng **M2**, ba hàng đầu tạo thành header structure:

- row $0$: title header
- row $1$: group header
- row $2$: column header

Ba hàng này được bold theo grammar. Các body rows phía sau giữ normal.

Last row của M2 được xử lý riêng bằng **stroke evidence**. Implementation lấy `stroke_scores` từ các non-empty text anchors trong last row. Merge markers và những vị trí không có score không tham gia quyết định.

Từ các valid scores, hệ thống tính:

$$

\operatorname{median}(s)

$$

Last row chỉ được bold khi có ít nhất một valid score và:

$$

\operatorname{median}(s)\ge 0.08

$$

Nếu không có valid scores hoặc median thấp hơn threshold, last row giữ normal.

Vì vậy, stroke evidence chỉ được sử dụng cho **M2 last-row decision**. Các bold rules còn lại đến từ cấu trúc bảng đã biết.

Khi một text value được xác định là bold, hệ thống bọc nó bằng Markdown syntax:

`value → **value**`

Formatting chỉ được áp dụng lên text-bearing anchors. Implementation bỏ qua `[[H]]`, `[[V]]`, empty values và những value đã được bọc `**...**`.

## 6.5 Extended Markdown Serialization

Sau Bold Recovery, cell matrix đã chứa đầy đủ các representation cần thiết cho output cuối. Ở bước này, serializer không tạo thêm merge semantics hay formatting mới. Nó chỉ chuyển các strings đang có trong matrix thành cú pháp Markdown table.

Cell matrix có thể đã chứa:

- recognized text tại anchors
- `[[H]]`, `[[V]]` để giữ merged-cell structure
- `<br>` để giữ line breaks trong cùng một cell
- `\|` cho pipes đã được escape từ bước Cell Recognition
- `*...**` cho text đã được xác định là bold

Với mỗi row, implementation nối các cell values bằng:

`" | "`

và thêm pipe ở hai đầu để tạo một Markdown row.

Sau row đầu tiên, hệ thống chèn một separator row:

`| --- | ... | --- |`

Cuối cùng, toàn bộ serialized rows được nối bằng:

`"\n"`

để tạo thành table hoàn chỉnh.

Serializer giữ nguyên mọi cell value đã có. Nó không suy luận lại merged cells, không split text lines, không escape pipe thêm lần nữa và không đưa ra quyết định formatting mới.

Ví dụ, nếu cell matrix đã chứa:

`Line 1<br>Line 2`

thì output vẫn giữ nguyên `<br>`.

Tương tự, `[[H]]`, `[[V]]`, `\|` và `**text**` đều được preserved verbatim trong Markdown output.

Output được gọi là **Extended Markdown** vì nó kết hợp cú pháp Markdown table thông thường với các merge markers riêng của dataset.
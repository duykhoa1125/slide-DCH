// Mở đầu & Lý thuyết chung (Slides 01–09)
(window.DECK_SLIDES = window.DECK_SLIDES || []).push(/* html */ `
<!-- 1 · COVER -->
<section class="slide" data-sec="Mở đầu" data-title="Trang bìa: Dinh dưỡng - đề phòng độc tố">
  <div class="slide-inner" style="padding:50px 58px 54px;justify-content:space-between">
    <div style="display:flex;align-items:center;gap:22px">
      <div class="imgwhite" style="--d:0;padding:14px 24px;flex:none">
        <img src="assets/images/01-logo-hcmut.png" alt="Logo Trường Đại học Bách khoa, Đại học Quốc gia Thành phố Hồ Chí Minh" style="width:470px;height:auto;display:block" />
      </div>
      <span class="scope-pill" style="margin-left:auto">HÓA · XÂY DỰNG · ĐIỆN · MÔI TRƯỜNG · DINH DƯỠNG</span>
    </div>
    <div style="display:flex;align-items:center;gap:56px;flex:1;min-height:0">
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:36px">
        <div class="bigtitle" style="font-family:var(--disp);font-weight:900;font-size:100px;line-height:1.12;letter-spacing:-.02em">
          DINH DƯỠNG<br/><span class="hl" style="background:var(--coral);color:#fff;padding:.05em .14em .16em;border-radius:.14em;display:inline-block;margin-top:.06em;animation:bob 3.4s ease-in-out infinite">ĐỀ PHÒNG</span><br/>ĐỘC TỐ
        </div>
        <p class="sub" style="font-size:30px;max-width:820px;margin-top:0">Nhận diện chất độc quanh ta mỗi ngày, và cách <b>dinh dưỡng</b> giúp cơ thể đứng vững trước chúng.</p>
      </div>
      <div class="imgbig" style="--d:1;width:600px;height:540px;flex:none;align-self:center">
        <img class="ph" style="object-position:center 20%" src="assets/images/01-cover-worker.webp" alt="Minh họa công nhân đeo mặt nạ phòng độc cầm bình hóa chất, phía sau là nhà máy và khói độc" />
        <span class="cap">Khói · bụi · hơi hóa chất, <b>mối nguy vô hình</b> nơi làm việc</span>
      </div>
    </div>
  </div>
</section>

<!-- 2 · THÀNH VIÊN NHÓM -->
<section class="slide" data-sec="Mở đầu" data-title="Thành viên nhóm">
  <div class="slide-inner">
    <div class="s-head"><div>
      <h2 class="title">Thành viên <span class="hl">nhóm</span></h2></div><span class="s-num">02</span></div>
    <div class="memtable">
      <div class="memrow head"><span>STT</span><span>Họ và tên</span><span>MSSV</span><span>Ngành</span></div>
      <div class="memrow" style="--d:0"><span class="stt">01</span><span class="nm">Nguyễn Tuấn Huy</span><span class="mssv">2411248</span><span class="ng">Kỹ thuật Hoá Học - Hoá Dược</span></div>
      <div class="memrow" style="--d:1"><span class="stt">02</span><span class="nm">Trần Nhật Văn</span><span class="mssv">2213919</span><span class="ng">Kỹ thuật Xây Dựng</span></div>
      <div class="memrow" style="--d:2"><span class="stt">03</span><span class="nm">Nguyễn Trần Đức Duy Khoa</span><span class="mssv">2311628</span><span class="ng">Máy tính</span></div>
      <div class="memrow" style="--d:3"><span class="stt">04</span><span class="nm">Đặng Thái Sơn</span><span class="mssv">2212933</span><span class="ng">Điện - Điện tử</span></div>
      <div class="memrow" style="--d:4"><span class="stt">05</span><span class="nm">Phan Phước Duy</span><span class="mssv">2410546</span><span class="ng">Cơ Khí</span></div>
      <div class="memrow" style="--d:5"><span class="stt">06</span><span class="nm">Nguyễn Anh Vũ</span><span class="mssv">2115323</span><span class="ng">Cơ Khí</span></div>
      <div class="memrow" style="--d:6"><span class="stt">07</span><span class="nm">Nguyễn Huỳnh Phúc Thịnh</span><span class="mssv">2313286</span><span class="ng">Điện - Điện tử</span></div>
    </div>
  </div>
</section>

<!-- 3 · LÝ DO CHỌN ĐỀ TÀI -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="Vì sao chọn đề tài này?">
  <div class="slide-inner" style="padding-left:118px;padding-right:118px">
    <div class="s-head"><div>
      <h2 class="title">Vì sao chọn <span class="hl">đề tài</span> này?</h2></div><span class="s-num">03</span></div>
    <div class="split">
      <div class="txtcol">
        <div class="statement" style="--d:0">Độc tố ở<br/>quanh ta<br/><span class="hl">mỗi ngày</span></div>
        <p style="font-size:30px;line-height:1.45;font-weight:500;margin-top:26px;max-width:560px">Trong thực phẩm, nước uống, không khí, và ngay tại nơi làm việc. Không ai đứng ngoài vòng phơi nhiễm.</p>
      </div>
      <div class="pts">
        <div class="pt" style="--d:1"><span class="n">01</span><div><h3>Bốn ngành, hai mặt</h3><p>Hóa, xây dựng, điện, môi trường vừa thúc đẩy kinh tế, vừa phát sinh nguy cơ nhiễm độc.</p></div></div>
        <div class="pt" style="--d:2"><span class="n">02</span><div><h3>Phòng ngừa là vàng</h3><p>Phòng ngừa chủ động luôn hiệu quả hơn xử lý hậu quả.</p></div></div>
        <div class="pt" style="--d:3"><span class="n g">03</span><div><h3>Dinh dưỡng là lá chắn</h3><p>Ăn uống hợp lý giúp giảm tác hại và tăng đào thải độc tố, nhưng không thay thế điều trị y tế.</p></div></div>
      </div>
    </div>
  </div>
</section>

<!-- 3 · MỤC TIÊU & PHẠM VI -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="Mục tiêu & phạm vi nghiên cứu">
  <div class="slide-inner fit4">
    <div class="s-head"><div>
      <h2 class="title">Mục tiêu &amp; <span class="hl y">phạm vi</span></h2></div><span class="s-num">04</span></div>
    <div class="scope2">
      <div class="scope-col">
        <p class="scope-head"><i></i>Mục tiêu</p>
        <div class="pts">
          <div class="pt" style="--d:0"><span class="n">01</span><div><h3>Hiểu bản chất</h3><p>Nắm khái niệm, phân loại và đường xâm nhập của độc tố.</p></div></div>
          <div class="pt" style="--d:1"><span class="n">02</span><div><h3>Nhận diện</h3><p>Chỉ mặt các độc tố thường gặp trong 4 ngành nghề.</p></div></div>
          <div class="pt" style="--d:2"><span class="n">03</span><div><h3>Làm rõ dinh dưỡng</h3><p>Vai trò của ăn uống + so sánh tháp dinh dưỡng xưa và nay.</p></div></div>
          <div class="pt" style="--d:3"><span class="n">04</span><div><h3>Đề xuất phòng ngừa</h3><p>Biện pháp cụ thể cho từng ngành, từng nhóm độc tố.</p></div></div>
        </div>
      </div>
      <div class="scope-col phamvi">
        <p class="scope-head"><i></i>Phạm vi</p>
        <div class="pts">
          <div class="pt" style="--d:4"><span class="n y">01</span><div><h3>Nội dung</h3><p>Độc tố trong ngành hóa, xây dựng, điện, môi trường và vai trò dinh dưỡng.</p></div></div>
          <div class="pt" style="--d:5"><span class="n y">02</span><div><h3>Đối tượng</h3><p>Người lao động và cộng đồng xung quanh.</p></div></div>
          <div class="pt" style="--d:6"><span class="n y">03</span><div><h3>Giới hạn</h3><p>Tổng quan lý thuyết, không đi sâu vào điều trị lâm sàng.</p></div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- 4 · KHÁI NIỆM -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="4 khái niệm cốt lõi">
  <div class="slide-inner">
    <div class="s-head"><div>
      <h2 class="title">4 khái niệm <span class="hl k">cốt lõi</span></h2></div><span class="s-num">05</span></div>
    <div class="pts tight" style="flex:1">
      <div class="pt" style="--d:0"><span class="n">01</span><div><h3>Độc chất học</h3><p>Ngành khoa học nghiên cứu tính chất và tác động của chất độc (tự nhiên, hóa học, sinh học) lên cơ thể sống và môi trường, cùng cách chẩn đoán, phòng ngừa, điều trị.</p></div></div>
      <div class="pt" style="--d:1"><span class="n">02</span><div><h3>Chất độc</h3><p>Chất khi vào cơ thể với lượng nhỏ trong điều kiện nhất định gây hại: từ nhẹ (đau đầu, buồn nôn) đến nặng (co giật, sốt cao), có thể tử vong.</p></div></div>
      <div class="pt" style="--d:2"><span class="n">03</span><div><h3>Ngộ độc</h3><p>Sự rối loạn của cơ thể dưới tác dụng của chất độc.</p></div></div>
      <div class="pt" style="--d:3"><span class="n">04</span><div><h3>Phơi nhiễm</h3><p>Cơ thể tiếp xúc với chất độc, bước đầu tiên của mọi hành trình nhiễm độc.</p></div></div>
    </div>
    <p class="foot" style="--d:4"><span class="bigword">Đường đi + liều lượng</span> quyết định mức độ nguy hiểm.</p>
  </div>
</section>

<!-- 5 · PHÂN LOẠI 1 -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="Phân loại theo nguồn gốc và dạng tác động">
  <div class="slide-inner fit5s">
    <div class="s-head"><div>
      <h2 class="title">Phân loại theo nguồn gốc và <span class="hl">dạng tác động</span></h2></div><span class="s-num">06</span></div>
    <div class="cols2">
      <div class="col5">
        <p class="col5-head"><i></i>Theo nguồn gốc</p>
        <div class="pts">
          <div class="pt" style="--d:0"><span class="cdot" style="background:var(--green)"></span><div><h3>Tự nhiên</h3></div></div>
          <div class="pt" style="--d:1"><span class="cdot" style="background:var(--coral)"></span><div><h3>Hóa học</h3><p>Kim loại nặng, dung môi, thuốc trừ sâu.</p></div></div>
          <div class="pt" style="--d:2"><span class="cdot" style="background:var(--yellow)"></span><div><h3>Sinh học</h3><p>Nọc độc rắn, ngoại độc tố và nội độc tố vi khuẩn.</p></div></div>
        </div>
      </div>
      <div class="col5 right">
        <p class="col5-head"><i></i>Theo dạng tác động</p>
        <div class="pts">
          <div class="pt" style="--d:0"><span class="n">01</span><div><h3>Hóa sinh</h3><p>Thay đổi phản ứng hóa sinh, enzyme và nội tiết trong cơ thể.</p></div></div>
          <div class="pt" style="--d:1"><span class="n">02</span><div><h3>Dinh dưỡng</h3><p>Ảnh hưởng khẩu phần và hấp thu: ăn nhiều cá biển lớn dễ tích lũy thủy ngân; uống trà sau ăn giảm hấp thu dưỡng chất.</p></div></div>
          <div class="pt" style="--d:2"><span class="n">03</span><div><h3>Gây ung thư · đột biến</h3><p>Tổn thương DNA, gen, benzen gây ung thư máu, tia UV gây ung thư da.</p></div></div>
          <div class="pt" style="--d:3"><span class="n">04</span><div><h3>Hành vi</h3><p>Tác động lên thần kinh, thường gây nghiện, điển hình là caffeine.</p></div></div>
          <div class="pt" style="--d:4"><span class="n">05</span><div><h3>Cơ quan</h3><p>Gây hại một cơ quan cụ thể: hơi hóa chất tẩy rửa → kích ứng hô hấp.</p></div></div>
        </div>
      </div>
    </div>
    <p class="foot" style="--d:5;margin-top:12px;padding-top:14px"><span class="bigword">Một chất, nhiều mặt:</span> cùng một độc tố có thể thuộc nhiều nhóm tác động cùng lúc.</p>
  </div>
</section>

<!-- 6 · PHÂN LOẠI 2 : MỨC ĐỘ & THỜI GIAN -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="Phân loại theo mức độ và thời gian">
  <div class="slide-inner fit6">
    <div class="s-head"><div>
      <h2 class="title">Phân loại theo mức độ và thời gian</h2></div><span class="s-num">07</span></div>
    <div class="split">
      <div class="txtcol" style="gap:30px">
        <div class="stat" style="--d:0"><div class="num" style="font-size:92px">LD<sub>50</sub></div>
          <p style="margin-top:8px">Liều gây chết <b>50%</b> động vật thí nghiệm. Đơn vị: <b>mg/kg</b>.</p></div>
        <div class="stat" style="--d:1"><div class="num" style="font-size:92px">LC<sub>50</sub></div>
          <p style="margin-top:8px">Nồng độ gây chết <b>50%</b> động vật thí nghiệm. Đơn vị: <b>mg/m³</b> hoặc <b>ppm</b>. Giá trị <b>càng thấp → chất càng độc</b>.</p></div>
        <div style="--d:2">
          <h3 style="font-family:var(--disp);font-weight:800;font-size:30px;margin-bottom:4px">Theo thời gian nhiễm độc</h3>
          <div class="tlevels">
            <p><b>Siêu cấp tính:</b> vài giây, như kali cyanide KCN.</p>
            <p><b>Cấp tính:</b> xảy ra trong vòng 24h, là triệu chứng lâm sàng (đau bụng do ăn thức ăn không đảm bảo vệ sinh).</p>
            <p><b>Bán cấp tính:</b> vài ngày đến vài tuần.</p>
            <p><b>Mạn tính:</b> vài tháng đến vài năm, do tích lũy kim loại kiềm thổ ở xương.</p>
          </div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;min-height:0">
        <div class="imgwhite" style="--d:1;flex:1"><img class="fill" src="assets/images/07-kcn-crystal.png" alt="Cấu trúc tinh thể kali cyanide KCN, ví dụ chất siêu cấp tính" /></div>
        <div class="toxscale" role="img" aria-label="Thang 5 cấp độ độc, từ độc nhất đến ít độc nhất: I-a cực độc, I-b rất độc, II độc, III nguy hiểm, IV cẩn thận">
          <div class="ts-head"><span class="t">5 cấp độ độc</span><span class="dir">Độc nhất → ít độc nhất</span></div>
          <div class="ts-bars">
            <div class="ts-lv" style="--d:2;--c:#8F0D04;--h:100%"><div class="bw"><i></i></div><b>I-a</b><span>cực độc</span></div>
            <div class="ts-lv" style="--d:3;--c:#C1270F;--h:80%"><div class="bw"><i></i></div><b>I-b</b><span>rất độc</span></div>
            <div class="ts-lv" style="--d:4;--c:#E8402F;--h:62%"><div class="bw"><i></i></div><b>II</b><span>độc</span></div>
            <div class="ts-lv" style="--d:5;--c:#F07B1D;--h:45%"><div class="bw"><i></i></div><b>III</b><span>nguy hiểm</span></div>
            <div class="ts-lv" style="--d:6;--c:#F5B921;--h:30%"><div class="bw"><i></i></div><b>IV</b><span>cẩn thận</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- 7 · ĐƯỜNG XÂM NHẬP -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="3 đường xâm nhập vào cơ thể">
  <div class="slide-inner">
    <div class="s-head"><div>
      <h2 class="title">Chất độc vào cơ thể <span class="hl g">bằng đường nào?</span></h2></div><span class="s-num">08</span></div>
    <div class="cols3">
      <div class="col" style="--d:0"><div class="n g">01</div><h3>Hô hấp, chủ yếu</h3><p>Khí, hơi, bụi vào phổi qua phế nang rồi thẳng vào máu.<span class="src">CO · SO₂ · hơi benzen, toluen · bụi chì · bụi mịn PM2.5</span></p></div>
      <div class="col" style="--d:1"><div class="n">02</div><h3>Tiêu hóa, chủ yếu</h3><p>Thức ăn, nước uống nhiễm độc; hấp thu ở ruột non vào máu.<span class="src">Kim loại nặng · thuốc trừ sâu trên rau củ · phụ gia</span></p></div>
      <div class="col" style="--d:2"><div class="n y">03</div><h3>Da &amp; niêm mạc</h3><p>Niêm mạc ở mắt, mũi, miệng, niêm mạc tai. Chất tan trong chất béo thấm qua da; chất phân cực kích ứng tại chỗ.<span class="src">Dung môi hữu cơ · thuốc trừ sâu</span></p></div>
    </div>
    <p class="foot" style="--d:3"><span class="bigword">Đường khác:</span> tiêm · vết cắn · vết thương hở, xâm nhập chủ động (ăn uống, tiêm) hoặc bị động (hít khí độc, thấm qua da).</p>
  </div>
</section>

<!-- 8 · HÀNH TRÌNH TRONG CƠ THỂ -->
<section class="slide" data-sec="Nhóm trưởng, Mở đầu · Lý thuyết · Kết luận" data-title="Đường đi của chất độc trong cơ thể">
  <div class="slide-inner">
    <div class="s-head"><div>
      <h2 class="title">Đường đi của <span class="hl">chất độc</span> trong cơ thể</h2></div><span class="s-num">09</span></div>
    <div class="fd-wrap">
      <p class="fd-side" style="--d:5">Chuyển hóa phụ thuộc gen, chủng tộc, giới tính, tuổi, bệnh lý, và <b>chế độ dinh dưỡng</b>: yếu tố <span class="bigword">có thể can thiệp được</span>.</p>
      <div class="flowdiag">
      <div class="fd-net" role="img" aria-label="Sơ đồ mạng: phơi nhiễm dẫn đến đi vào cơ thể rồi hấp thu và phân bố. Hấp thu và phân bố qua lại hai chiều với chuyển hóa và tích lũy, đồng thời dẫn đến gây độc và bài tiết. Chuyển hóa dẫn đến gây độc, tích lũy và bài tiết. Tích lũy dẫn đến bài tiết. Các đường đi vào cơ thể: tiêu hóa, hô hấp, vết thương, niêm mạc, tai, da.">
      <svg viewBox="0 0 1480 640" aria-hidden="true">
        <defs>
          <marker id="fdAh" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="4.6" markerHeight="4.6" orient="auto-start-reverse"><path d="M1.5 1.5 L10.5 6 L1.5 10.5 Z" fill="#E8402F"/></marker>
        </defs>
        <g class="fd-ln" style="--d:2" fill="none" stroke="#16130F" stroke-width="4" stroke-linecap="round">
          <path d="M620 80 V108" marker-end="url(#fdAh)"/>
          <path d="M620 186 V218" marker-end="url(#fdAh)"/>
        </g>
        <g class="fd-ln" style="--d:3" fill="none" stroke="#16130F" stroke-width="4" stroke-linecap="round">
          <path d="M472 302 L218 386" marker-end="url(#fdAh)"/>
          <path d="M768 302 L1252 386" marker-end="url(#fdAh)"/>
          <path d="M700 306 V348 H905 V386" marker-start="url(#fdAh)" marker-end="url(#fdAh)"/>
          <path d="M1046 428 H1162" marker-end="url(#fdAh)"/>
        </g>
        <g class="fd-ln" style="--d:4" fill="none" stroke="#16130F" stroke-width="4" stroke-linecap="round">
          <path d="M520 306 V530" marker-start="url(#fdAh)" marker-end="url(#fdAh)"/>
          <path d="M432 530 L218 470" marker-end="url(#fdAh)"/>
          <path d="M612 530 L842 470" marker-end="url(#fdAh)"/>
          <path d="M684 582 L1242 470" marker-end="url(#fdAh)"/>
        </g>
        <g class="fd-ln" style="--d:1">
          <path d="M884 16 H860 V198 H884" fill="none" stroke="#16130F" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
          <text class="rt-t" x="908" y="40">Tiêu hóa</text>
          <text class="rt-t" x="908" y="69">Hô hấp</text>
          <text class="rt-t" x="908" y="98">Vết thương</text>
          <text class="rt-t" x="908" y="127">Niêm mạc</text>
          <text class="rt-t" x="908" y="156">Tai</text>
          <text class="rt-t" x="908" y="185">Da</text>
        </g>
        <g class="fd-nd" style="--d:0">
          <rect x="477" y="13" width="300" height="72" rx="16" fill="#16130F"/>
          <rect x="470" y="6" width="300" height="72" rx="16" fill="#16130F"/>
          <text class="nd-t w" x="620" y="42" dominant-baseline="central">Phơi nhiễm</text>
        </g>
        <g class="fd-nd" style="--d:1">
          <rect x="452" y="119" width="350" height="72" rx="16" fill="#16130F"/>
          <rect x="445" y="112" width="350" height="72" rx="16" fill="#FFFDF7" stroke="#16130F" stroke-width="3"/>
          <text class="nd-t" x="620" y="148" dominant-baseline="central">Đi vào cơ thể</text>
        </g>
        <g class="fd-nd" style="--d:2">
          <rect x="407" y="229" width="440" height="80" rx="16" fill="#16130F"/>
          <rect x="400" y="222" width="440" height="80" rx="16" fill="#E8402F"/>
          <text class="nd-t w" x="620" y="262" dominant-baseline="central">Hấp thu và phân bố</text>
        </g>
        <g class="fd-nd" style="--d:3">
          <rect x="47" y="397" width="270" height="76" rx="16" fill="#16130F"/>
          <rect x="40" y="390" width="270" height="76" rx="16" fill="#FFFDF7" stroke="#16130F" stroke-width="3"/>
          <text class="nd-t" x="175" y="428" dominant-baseline="central">Gây độc</text>
        </g>
        <g class="fd-nd" style="--d:3">
          <rect x="777" y="397" width="270" height="76" rx="16" fill="#16130F"/>
          <rect x="770" y="390" width="270" height="76" rx="16" fill="#FFFDF7" stroke="#16130F" stroke-width="3"/>
          <text class="nd-t" x="905" y="428" dominant-baseline="central">Tích lũy</text>
        </g>
        <g class="fd-nd" style="--d:3">
          <rect x="1177" y="397" width="270" height="76" rx="16" fill="#16130F"/>
          <rect x="1170" y="390" width="270" height="76" rx="16" fill="#FFFDF7" stroke="#16130F" stroke-width="3"/>
          <text class="nd-t" x="1305" y="428" dominant-baseline="central">Bài tiết</text>
        </g>
        <g class="fd-nd" style="--d:4">
          <rect x="367" y="541" width="320" height="76" rx="16" fill="#16130F"/>
          <rect x="360" y="534" width="320" height="76" rx="16" fill="#FFFDF7" stroke="#16130F" stroke-width="3"/>
          <text class="nd-t" x="520" y="572" dominant-baseline="central">Chuyển hóa</text>
        </g>
      </svg>
      </div>
      </div>
    </div>
  </div>
</section>

`);

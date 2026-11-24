// Danh mục nguồn đối chiếu từ đúng 5 tài liệu thành viên đã nộp (P2-02)
(function (global) {
  'use strict';

  var SOURCE_GROUPS = [
    {
      group: 'Phần 0 · Mở đầu & Lý thuyết (Nhóm trưởng — Phần mở đầu và nền tảng lý thuyết.docx)',
      rows: [
        { slide: '03–08', item: 'Lý do, mục tiêu, khái niệm, phân loại, đường xâm nhập', ref: 'Phần mở đầu và nền tảng lý thuyết.docx, Slide 1–6', status: 'ok', note: 'Không chứa URL ngoài; bám sát văn bản và hình KCN (Slide 5)' },
        { slide: '09', item: 'Sơ đồ đường đi của chất độc (image2.png) & liệt kê đào thải', ref: 'Phần mở đầu và nền tảng lý thuyết.docx, Slide 7', status: 'ok', note: 'Hình vẽ tay gốc không kèm URL' }
      ]
    },
    {
      group: 'Phần 1 · Dinh dưỡng (Người 1 — Phần dinh dưỡng.docx)',
      rows: [
        { slide: '11', item: 'Ảnh & nội dung Quyết định 1982/QĐ-BYT (01/7/2026)', ref: 'Phần dinh dưỡng.docx, Phần A Slide 1 (chú thích 1)', url: 'https://thuvienphapluat.vn/van-ban/The-thao-Y-te/Quyet-dinh-1982-QD-BYT-2026-Huong-dan-chuyen-mon-bien-phap-thuc-hien-dinh-duong-phong-benh-713081.aspx', label: 'Thư viện Pháp luật · QĐ 1982/QĐ-BYT', status: 'ok' },
        { slide: '12', item: 'Hình vai trò của gan (image3.jpg) & số liệu >500 chức năng', ref: 'Phần dinh dưỡng.docx, Phần A Slide 2 (chú thích 2; văn bản nêu Healthline, 2025)', url: 'https://visuckhoecongdong.vn/cach-giai-doc-gan-tai-nha-don-gian-va-hieu-qua/', label: 'Vì sức khỏe cộng đồng (25/09/2024)', status: 'ok', note: 'Healthline (2025) được nêu trong văn bản nhưng không có URL trong DOCX' },
        { slide: '13–16', item: 'Ảnh minh họa gan, chống oxy hóa, chất xơ (image4–7)', ref: 'Phần dinh dưỡng.docx, Phần A Slide 3–7', status: 'ok', note: 'Ảnh nhúng trong DOCX không có URL nguồn' },
        { slide: '17', item: 'Ảnh sạp trái cây (17-nguon-thuc-pham.jpg)', ref: 'Ảnh minh họa sẵn của HTML (SLIDE 6 gốc dùng ảnh đã đặt ở Slide 15)', status: 'note', note: 'Chưa xác định URL gốc — không nằm trong 5 tài liệu nguồn' },
        { slide: '18', item: 'Bảng 6 vi chất thiết yếu & giới hạn UL', ref: 'Phần dinh dưỡng.docx, Phần A Slide 8 (trang 4–5)', status: 'ok', note: 'Không có URL trong DOCX' },
        { slide: '19 (trái)', item: 'Tháp dinh dưỡng truyền thống (2016–2020)', ref: 'Phần dinh dưỡng.docx, Phần B Slide 1 (chú thích 3)', url: 'https://dinhduongmevabe.com.vn/danh-cho-can-bo-y-te/tai-lieu-ho-tro-tu-van-dinh-duong/52-thap-dinh-duong-hop-ly-cho-nguoi-truong-thanh-giai-doan-2016-2020', label: 'Dinh dưỡng Bà mẹ & Trẻ em', status: 'ok' },
        { slide: '19 (phải)', item: 'Tháp dinh dưỡng hiện nay (2021–2030)', ref: 'Phần dinh dưỡng.docx, Phần B Slide 2 (chú thích 4)', url: 'https://viendinhduongtphcm.org/vi/y-hoc-thuong-thuc/bo-7-thap-dinh-duong-moi-nhat-tu-vien-dinh-duong-quoc-gia.html', label: 'Viện NCDD TP.HCM (08/04/2026)', status: 'ok' },
        { slide: '20, 22', item: 'Báo Đại Đoàn Kết (8,1 g muối/ngày)', ref: 'Phần dinh dưỡng.docx, Phần B Slide 4 (chú thích 5)', url: 'https://daidoanket.vn/nguoi-viet-dang-an-muoi-gan-gap-doi-khuyen-nghi.html', label: 'Dương Toàn · Đại Đoàn Kết (05/11/2026)', status: 'ok' },
        { slide: '20, 22', item: 'Báo VnExpress (>60% thiếu rau quả)', ref: 'Phần dinh dưỡng.docx, Phần B Slide 4 (chú thích 6)', url: 'https://vnexpress.net/rau-qua-doi-dao-nguoi-viet-van-an-thieu-5090234.html', label: 'Lê Phương · VnExpress (26/06/2026)', status: 'ok' },
        { slide: '20, 22', item: 'Báo Sức khỏe & Đời sống (20 triệu người thừa cân – béo phì)', ref: 'Phần dinh dưỡng.docx, Phần B Slide 4 (chú thích 7)', url: 'https://suckhoedoisong.vn/20-trieu-nguoi-viet-dang-song-chung-voi-thua-can-beo-phi-nguy-co-doi-dien-nhieu-benh-169260306212041203.htm', label: 'Thái Bình · Sức khỏe & Đời sống (06/03/2026)', status: 'ok' },
        { slide: '23', item: 'Ảnh & bài Thời báo VTV về tháp dinh dưỡng 2026', ref: 'Phần dinh dưỡng.docx, Phần B Slide 5 (chú thích 8)', url: 'https://vtv.vn/nhung-thay-doi-tich-cuc-tu-thap-dinh-duong-nam-2026-100260306093948687.htm', label: 'Nhã Khanh · Thời báo VTV (08/03/2026)', status: 'ok' }
      ]
    },
    {
      group: 'Phần 2 · Ngành hóa (Người 2 — Ngành hóa.pdf)',
      rows: [
        { slide: '24', item: 'Ảnh nhà máy hóa chất (24-nha-may-hoa-chat.jpg)', ref: 'Khác với Hình 18 trong Ngành hóa.pdf (tr. 10)', status: 'note', note: 'Chưa xác định URL ảnh đang hiển thị (không gán nhầm URL Hình 18)' },
        { slide: '25', item: 'Ảnh tháp chưng cất (Hình 3)', ref: 'Ngành hóa.pdf, Slide 3 tr. 2 (chú thích 3)', url: 'https://www.istockphoto.com/vi/b%E1%BB%A9c-%E1%BA%A3nh/distillation-columns-at-a-petrochemical-plant', label: 'iStock · Distillation columns', status: 'ok' },
        { slide: '26', item: 'Công thức cấu tạo Benzen C₆H₆ (Hình 2)', ref: 'Ngành hóa.pdf, Slide 2 tr. 2 (chú thích 2)', url: 'https://byjus.com/chemistry/structure-of-benzene/', label: 'BYJU\'S · Structure of Benzene', status: 'ok' },
        { slide: '27', item: 'Mô hình phân tử Toluen 3D (27-toluen-c7h8.png)', ref: 'Khác với Hình 6 trong Ngành hóa.pdf (tr. 4, vichem.vn)', status: 'note', note: 'Chưa xác định URL ảnh 3D đang dùng (không gán nhầm URL Hình 6)' },
        { slide: '28', item: '5 ảnh kim loại: Pb, Hg, Cd (từ XÂY DỰNG ĐIỆN2.docx); As, Cu (ảnh khác)', ref: 'XÂY DỰNG ĐIỆN2.docx (SLIDE 7); As & Cu khác Hình 23, 27 trong Ngành hóa.pdf', status: 'note', note: 'Pb/Hg/Cd khớp DOCX Người 3 (không URL); As/Cu chưa xác định URL gốc' },
        { slide: '29', item: 'Ảnh bể tẩy gỉ kim loại (Hình 32)', ref: 'Ngành hóa.pdf, Slide 16 tr. 17 (chú thích 32)', url: 'https://www.protank.com/custom-pickling-tanks', label: 'ProTank · Pickling tanks', status: 'ok' },
        { slide: '30', item: 'Ảnh ván gỗ ép công nghiệp (Hình 39)', ref: 'Ngành hóa.pdf, Slide 20 tr. 21 (chú thích 39)', url: 'https://silamas.com/mdf-plant-particle-board-plant/', label: 'Silamas · MDF plant', status: 'ok' },
        { slide: '34', item: 'Ảnh trang bị PPE hóa chất (Hình 53)', ref: 'Ngành hóa.pdf, Slide 30 tr. 30 (chú thích 53)', url: 'https://www.sirsafety.com/safety-gloves-chemical-protective-gloves', label: 'SirSafety · Chemical PPE', status: 'ok' }
      ]
    },
    {
      group: 'Phần 3 · Xây dựng & Điện (Người 3 — XÂY DỰNG ĐIỆN2.docx)',
      rows: [
        { slide: '37, 41, 43', item: 'Ảnh công nhân xây dựng, thợ điện cao áp, mô hình SF₆', ref: 'XÂY DỰNG ĐIỆN2.docx (image5, image10, image9)', status: 'ok', note: 'Ảnh nhúng trong DOCX Người 3 (tài liệu không ghi URL)' },
        { slide: '36, 38, 39, 42', item: 'Ảnh công trường, bụi silica, hàn xây dựng, hàn mạch điện tử', ref: 'Ảnh minh họa sẵn của HTML (không nằm trong XÂY DỰNG ĐIỆN2.docx)', status: 'note', note: 'Chưa xác định URL ảnh' }
      ]
    },
    {
      group: 'Phần 4 · Môi trường & Kết luận (Người 4 — Phần 4.docx)',
      rows: [
        { slide: '46', item: 'Hình 1 · Ô nhiễm môi trường công nghiệp', ref: 'Phần 4.docx, Slide 1 (tr. 1)', url: 'https://waradana.com/article/260317-%D8%A3%D9%83%D8%AB%D8%B1-%D9%85%D8%B5%D8%A7%D8%AF%D8%B1-%D8%A7%D9%84%D8%AA%D9%84%D9%88%D8%AB-%D8%AE%D8%B7%D9%88%D8%B1%D8%A9-%D8%B9%D9%84%D9%89-%D8%A7%D9%84%D8%A3%D8%B1%D8%B6', label: 'Waradana', status: 'ok' },
        { slide: '47', item: 'Hình 2 · Ô nhiễm không khí do khí thải', ref: 'Phần 4.docx, Slide 2 (tr. 2)', url: 'https://www.bild.de/ratgeber/2020/ratgeber/luftverschmutzung-raubt-uns-2-9-jahre-lebenszeit-69220254.bild.html', label: 'Bild (2020)', status: 'ok' },
        { slide: '48', item: 'Hình 3 · Nước thải xả trực tiếp vào nguồn nước', ref: 'Phần 4.docx, Slide 3 (tr. 3)', url: 'https://sita.sk/klima/znecistenie-z-nasich-kupelni-chemikalie-proti-blcham-zaplavuju-rieky-a-ohrozuju-ekosystemy/', label: 'SITA.sk', status: 'ok' },
        { slide: '49', item: 'Hình 4 · Phun thuốc BVTV & Hình 5 · Cấu tạo Chlorpyrifos', ref: 'Phần 4.docx, Slide 4 (tr. 4)', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/2730', label: 'UseForesight (Hình 4) & PubChem 2730 (Hình 5)', status: 'ok' },
        { slide: '49', item: 'Hình 6 · Xử lý đất dioxin Biên Hòa & Hình 7 · Cấu tạo 2,3,7,8-TCDD', ref: 'Phần 4.docx, Slide 5 (tr. 5)', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/15625', label: 'Vietnam.vn (Hình 6) & PubChem 15625 (Hình 7)', status: 'ok' },
        { slide: '50', item: 'Hình 8 · Vi nhựa ven biển (Hình 9 · PE là SVG từ công thức DOCX)', ref: 'Phần 4.docx, Slide 6 (tr. 6)', url: 'https://response.restoration.noaa.gov/sites/default/files/styles/annual_report_image/public/images/%5Buid%5D/microplastics.jpg?itok=Q_B5pDWA', label: 'NOAA (Hình 8)', status: 'ok', note: 'Hình 9 (PE) không có URL trong DOCX' },
        { slide: '51–52', item: 'Slide 51 dùng lại ảnh Phần 1 (nội dung tham chiếu WHO); Slide 52 dùng Hình 10 WHO', ref: 'Phần 4.docx, Slide 7 (tr. 7)', url: 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet', label: 'WHO · Healthy diet (Hình 10)', status: 'ok', note: 'Ảnh ở Slide 51 tái sử dụng từ Phần 1; Hình 10 WHO nằm ở Slide 52' }
      ]
    }
  ];

  function renderSources(container) {
    if (!container) return;
    container.innerHTML = SOURCE_GROUPS.map(function (grp) {
      var rowsHtml = grp.rows.map(function (r) {
        var badge = r.status === 'ok'
          ? '<span class="src-badge ok">Khớp nguồn</span>'
          : '<span class="src-badge note">Chưa xác định URL</span>';
        var linkHtml = r.url
          ? '<a class="src-link" href="' + r.url + '" target="_blank" rel="noopener noreferrer">' + (r.label || r.url) + '</a>'
          : '<span style="opacity:.7">Không có URL trong tài liệu</span>';
        var noteHtml = r.note ? '<div style="font-size:13px;opacity:.78;margin-top:3px">' + r.note + '</div>' : '';
        return '<tr><td><b>' + r.slide + '</b></td><td>' + r.item + '</td><td>' + r.ref + '</td><td>' + linkHtml + noteHtml + '</td><td>' + badge + '</td></tr>';
      }).join('');
      return '<div class="src-group"><h3>' + grp.group + '</h3>' +
        '<table class="src-table"><thead><tr><th style="width:90px">Slide</th><th style="width:27%">Hình / nội dung</th><th style="width:24%">Vị trí tài liệu</th><th>Đường dẫn / ghi chú</th><th style="width:130px">Trạng thái</th></tr></thead><tbody>' +
        rowsHtml + '</tbody></table></div>';
    }).join('');
  }

  global.DeckSources = {
    render: renderSources
  };
})(window);

import json

with open('/home/user/preview_images.json', 'r') as f:
    preview_data = json.load(f)

p1 = preview_data['pages'][0]
p2 = preview_data['pages'][1]
p3 = preview_data['pages'][2]

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EthioFormat — Automated Ethiopian Thesis Formatting SaaS</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background-color: #f8fafc; color: #0f172a; line-height: 1.5; }}
    .header {{ position: sticky; top: 0; z-index: 40; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(8px); border-bottom: 1px solid #e2e8f0; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }}
    .logo-box {{ display: flex; align-items: center; gap: 10px; }}
    .logo-icon {{ width: 38px; height: 38px; background: linear-gradient(135deg, #059669, #10b981); color: white; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px; }}
    .badge {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 9999px; display: inline-block; margin-left: 6px; }}
    .hero {{ text-align: center; padding: 40px 20px 30px; background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%); border-bottom: 1px solid #e2e8f0; }}
    .hero h1 {{ font-size: 2.2rem; font-weight: 900; color: #0f172a; margin-bottom: 12px; }}
    .hero h1 span {{ background: linear-gradient(90deg, #059669, #0d9488); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .hero p {{ font-size: 1rem; color: #475569; max-width: 680px; margin: 0 auto 20px; }}
    .badge-bar {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; font-size: 12px; font-weight: 600; color: #334155; }}
    .badge-item {{ background: white; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
    
    .container {{ max-width: 900px; margin: -20px auto 40px; padding: 0 16px; }}
    .card {{ background: white; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08); padding: 28px; margin-bottom: 24px; }}
    .form-group {{ margin-bottom: 20px; }}
    .form-label {{ display: block; font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }}
    select, input[type="text"], input[type="email"], input[type="tel"] {{ width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; background: white; outline: none; transition: border 0.2s; }}
    select:focus, input:focus {{ border-color: #059669; box-shadow: 0 0 0 3px rgba(5,150,105,0.15); }}
    
    .custom-box {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; margin-top: 14px; display: none; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    
    .upload-zone {{ border: 2px dashed #94a3b8; border-radius: 14px; padding: 24px; text-align: center; background: #f8fafc; cursor: pointer; transition: all 0.2s; }}
    .upload-zone:hover {{ border-color: #059669; background: #f0fdf4; }}
    .btn-sample {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; float: right; }}
    
    .btn-primary {{ width: 100%; background: linear-gradient(90deg, #059669, #0d9488); color: white; border: none; padding: 14px 20px; border-radius: 12px; font-size: 15px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 12px rgba(5,150,105,0.25); transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }}
    .btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(5,150,105,0.35); }}
    
    /* Modal Styles */
    .modal-overlay {{ display: none; position: fixed; inset: 0; z-index: 50; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(4px); align-items: center; justify-content: center; padding: 16px; overflow-y: auto; }}
    .modal-box {{ background: white; border-radius: 20px; max-width: 860px; width: 100%; max-height: 90vh; overflow-y: auto; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }}
    .modal-header {{ background: #0f172a; color: white; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; border-top-left-radius: 20px; border-top-right-radius: 20px; }}
    .close-btn {{ background: transparent; border: none; color: #94a3b8; font-size: 24px; cursor: pointer; }}
    .close-btn:hover {{ color: white; }}
    
    /* Viewer */
    .viewer-toolbar {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0; }}
    .tab-btn {{ background: white; border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: bold; cursor: pointer; }}
    .tab-btn.active {{ background: #059669; color: white; border-color: #059669; }}
    
    .page-display {{ background: #e2e8f0; padding: 20px; text-align: center; min-height: 480px; display: flex; align-items: center; justify-content: center; }}
    .page-img {{ max-width: 100%; max-height: 580px; border-radius: 6px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); background: white; }}
    
    /* Paywall Hook */
    .paywall-hook {{ background: linear-gradient(180deg, #0f172a 0%, #020617 100%); color: white; padding: 28px; border-radius: 16px; margin: 24px; text-align: center; border: 2px solid rgba(16, 185, 129, 0.4); }}
    .price-box {{ background: rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 20px; margin: 16px 0; font-size: 13px; text-align: left; }}
    .btn-pay {{ background: linear-gradient(90deg, #10b981, #059669); color: white; border: none; padding: 14px 28px; border-radius: 12px; font-size: 15px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); display: inline-flex; align-items: center; gap: 8px; }}
    
    /* Checkout Modal */
    .checkout-box {{ display: none; background: white; border-radius: 16px; padding: 24px; margin: 20px; border: 1px solid #e2e8f0; text-align: left; }}
    .success-box {{ display: none; background: #ecfdf5; border: 2px solid #059669; border-radius: 16px; padding: 24px; text-align: center; margin: 20px; }}
  </style>
</head>
<body>

  <header class="header">
    <div class="logo-box">
      <div class="logo-icon">🎓</div>
      <div>
        <strong style="font-size: 18px; color: #0f172a;">Ethio<span style="color: #059669;">Format</span></strong>
        <span class="badge">ኢትዮ-ፎርማት v1.0</span>
      </div>
    </div>
    <div style="font-size: 12px; font-weight: 600; color: #059669;">
      🛡️ 22 Ethiopian Universities Standard
    </div>
  </header>

  <section class="hero">
    <span class="badge" style="margin-bottom: 12px; padding: 4px 12px;">Automated Ethiopian Academic Thesis Formatter</span>
    <h1>Format Your Academic Thesis in Seconds.<br><span>Zero Layout Errors.</span></h1>
    <p>Standardized thesis formatting following official School of Graduate Studies guidelines for Addis Ababa University, Jimma University, Hawassa University, and 20+ universities.</p>
    <div class="badge-bar">
      <div class="badge-item">✓ 1.5" Left Binding Margins</div>
      <div class="badge-item">✓ Times New Roman 12pt / 1.5 Spacing</div>
      <div class="badge-item">✓ Auto Chapter TOC & Dot Leaders</div>
      <div class="badge-item">✓ Free 3-Page Instant Preview</div>
    </div>
  </section>

  <div class="container">
    <div class="card">
      <h2 style="font-size: 18px; font-weight: 800; margin-bottom: 6px;">Select University & Upload Document</h2>
      <p style="font-size: 12px; color: #64748b; margin-bottom: 20px;">All parameters are strictly configured via dropdown menus (Zero manual user input errors).</p>

      <form id="formatterForm" onsubmit="event.preventDefault(); openPreviewModal();">
        <div class="form-group">
          <label class="form-label">University Preset Guidelines (የዩኒቨርሲቲ ምርጫ) *</label>
          <select id="universitySelect" onchange="toggleCustomMode(this.value)">
            <option value="aau">Addis Ababa University (አዲስ አበባ ዩኒቨርሲቲ)</option>
            <option value="ju">Jimma University (ጅማ ዩኒቨርሲቲ)</option>
            <option value="hu">Hawassa University (ሐዋሳ ዩኒቨርሲቲ)</option>
            <option value="bdu">Bahir Dar University (ባሕር ዳር ዩኒቨርሲቲ)</option>
            <option value="uog">University of Gondar (ጎንደር ዩኒቨርሲቲ)</option>
            <option value="amu">Arba Minch University (አርባ ምንጭ ዩኒቨርሲቲ)</option>
            <option value="haramaya">Haramaya University (ሀረማያ ዩኒቨርሲቲ)</option>
            <option value="astu">Adama Science and Technology University - ASTU (አዳማ ሳይንስና ቴክኖሎጂ)</option>
            <option value="aastu">Addis Ababa Science and Technology University - AASTU (አዲስ አበባ ሳይንስና ቴክኖሎጂ)</option>
            <option value="mu">Mekelle University (መቀሌ ዩኒቨርሲቲ)</option>
            <option value="du">Dilla University (ዲላ ዩኒቨርሲቲ)</option>
            <option value="dmu">Debre Markos University (ደብረ ማርቆስ ዩኒቨርሲቲ)</option>
            <option value="dbu">Debre Birhan University (ደብረ ብርሃን ዩኒቨርሲቲ)</option>
            <option value="wu">Wollo University (ወሎ ዩኒቨርሲቲ)</option>
            <option value="ddu">Dire Dawa University (ድሬዳዋ ዩኒቨርሲቲ)</option>
            <option value="jju">Jigjiga University (ጅግጅጋ ዩኒቨርሲቲ)</option>
            <option value="wollega">Wollega University (ወለጋ ዩኒቨርሲቲ)</option>
            <option value="ambo">Ambo University (አምቦ ዩኒቨርሲቲ)</option>
            <option value="mettu">Mettu University (መቱ ዩኒቨርሲቲ)</option>
            <option value="gambella">Gambella University (ጋምቤላ ዩኒቨርሲቲ)</option>
            <option value="smu">St. Mary's University (ቅድስት ማርያም ዩኒቨርሲቲ)</option>
            <option value="unity">Unity University (ዩኒቲ ዩኒቨርሲቲ)</option>
            <option value="custom">Custom Setup (የተለየ ህግ ለመምረጥ) ⚙️</option>
          </select>
        </div>

        <div id="customBox" class="custom-box">
          <strong style="font-size: 13px; color: #92400e; display: block; margin-bottom: 10px;">Mode B: Secondary Dropdown Rules (Locked Choices)</strong>
          <div class="grid-2">
            <div>
              <label class="form-label" style="font-size: 11px;">Font Family</label>
              <select><option>Times New Roman</option><option>Arial</option></select>
            </div>
            <div>
              <label class="form-label" style="font-size: 11px;">Font Size</label>
              <select><option>12 pt</option><option>11 pt</option></select>
            </div>
            <div>
              <label class="form-label" style="font-size: 11px;">Line Spacing</label>
              <select><option>1.5 Lines</option><option>2.0 Lines</option><option>1.0 Line</option></select>
            </div>
            <div>
              <label class="form-label" style="font-size: 11px;">Margins</label>
              <select><option>Ethiopian Standard (Left 1.5", Others 1.0")</option><option>Equal Margins (1.0" All Sides)</option></select>
            </div>
          </div>
        </div>

        <div class="form-group" style="margin-top: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <label class="form-label" style="margin: 0;">Upload Academic Thesis (.docx) *</label>
            <button type="button" class="btn-sample" onclick="loadSampleDoc()">📄 Sample AAU Thesis Loaded</button>
          </div>
          <div class="upload-zone" onclick="loadSampleDoc()">
            <div style="font-size: 28px; margin-bottom: 6px;">📄</div>
            <strong id="fileTitle" style="font-size: 14px; color: #0f172a;">Sample_AAU_MSc_Thesis.docx</strong>
            <p id="fileDesc" style="font-size: 12px; color: #059669; margin-top: 4px;">✓ Ready for formatting (38.8 KB • 5 Pages)</p>
          </div>
        </div>

        <button type="submit" class="btn-primary">
          ✨ Format Thesis & View 3-Page Free Preview
        </button>
      </form>
    </div>
  </div>

  <!-- Preview Modal -->
  <div id="previewModal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <div>
          <strong id="modalDocTitle">Sample_AAU_MSc_Thesis.docx</strong>
          <div style="font-size: 11px; color: #a7f3d0;" id="modalUnivName">Addis Ababa University (አዲስ አበባ ዩኒቨርሲቲ) • 5 Pages</div>
        </div>
        <button class="close-btn" onclick="closePreviewModal()">&times;</button>
      </div>

      <div class="viewer-toolbar">
        <div style="display: flex; gap: 8px;">
          <button class="tab-btn active" id="tab0" onclick="showPage(0)">Page 1: Cover</button>
          <button class="tab-btn" id="tab1" onclick="showPage(1)">Page 2: Approval</button>
          <button class="tab-btn" id="tab2" onclick="showPage(2)">Page 3: TOC</button>
          <span style="font-size: 11px; padding: 6px 10px; background: #e2e8f0; border-radius: 6px; font-weight: bold; color: #475569;">+ 2 Locked Pages</span>
        </div>
        <span style="font-size: 11px; font-weight: bold; color: #059669;">Free Preview Active</span>
      </div>

      <div class="page-display">
        <img id="mainPageImg" class="page-img" src="{p1}" alt="Thesis Page Preview">
      </div>

      <!-- Blurred Paywall Section -->
      <div id="paywallContainer" class="paywall-hook">
        <span class="badge" style="background: rgba(16,185,129,0.2); color: #6ee7b7; border-color: rgba(16,185,129,0.4); margin-bottom: 10px;">
          🔒 Paywall Protected • 2 Remaining Pages Locked
        </span>
        <h3 style="font-size: 20px; font-weight: 900; margin-bottom: 6px;">Unlock & Download Full Formatted Document</h3>
        <p style="font-size: 13px; color: #cbd5e1; max-width: 500px; margin: 0 auto;">
          Pages 1, 2, and 3 are previewed above. To download the complete, publication-ready formatted Word (.docx) document, complete payment.
        </p>

        <div class="price-box">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>Base Formatting Fee (Up to 20 Pages):</span>
            <strong>50.00 ETB</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 6px; color: #6ee7b7; font-size: 14px; font-weight: bold;">
            <span>Total Formatting Fee:</span>
            <span>50.00 ETB</span>
          </div>
        </div>

        <button class="btn-pay" onclick="openCheckout()">
          💳 Pay 50.00 ETB via Chapa / Telebirr
        </button>
      </div>

      <!-- Checkout Form -->
      <div id="checkoutBox" class="checkout-box">
        <h4 style="font-size: 16px; font-weight: 800; color: #0f172a; margin-bottom: 12px;">Chapa / Telebirr Instant Checkout</h4>
        <div class="grid-2" style="margin-bottom: 10px;">
          <div>
            <label class="form-label" style="font-size: 11px;">First Name</label>
            <input type="text" value="Abebe" id="cFirstName">
          </div>
          <div>
            <label class="form-label" style="font-size: 11px;">Last Name</label>
            <input type="text" value="Bikila" id="cLastName">
          </div>
        </div>
        <div style="margin-bottom: 10px;">
          <label class="form-label" style="font-size: 11px;">Email Address</label>
          <input type="email" value="student@aau.edu.et" id="cEmail">
        </div>
        <div style="margin-bottom: 14px;">
          <label class="form-label" style="font-size: 11px;">Phone Number (Telebirr / CBE)</label>
          <input type="tel" value="0911223344" id="cPhone">
        </div>
        <button class="btn-primary" onclick="simulatePayment()">
          🔒 Confirm 50.00 ETB & Download Formatted .DOCX
        </button>
      </div>

      <!-- Success Download Card -->
      <div id="successBox" class="success-box">
        <div style="font-size: 40px; margin-bottom: 8px;">🎉</div>
        <h3 style="font-size: 18px; font-weight: 900; color: #065f46; margin-bottom: 4px;">Payment Verified & Complete!</h3>
        <p style="font-size: 12px; color: #047857; margin-bottom: 16px;">Your full thesis has been uploaded to Supabase Storage and compiled with institutional guidelines.</p>
        
        <div style="background: white; border-radius: 12px; padding: 12px; margin-bottom: 16px; border: 1px solid #a7f3d0; text-align: left; font-size: 12px;">
          <strong>📄 Formatted_Sample_AAU_MSc_Thesis.docx</strong><br>
          <span style="color: #64748b;">39.6 KB • Microsoft Word Document • Signed 24h Link</span>
        </div>

        <a id="downloadBtn" href="/api/backend/download/sess_latest" style="text-decoration: none;" class="btn-primary" onclick="alert('Downloading full formatted .docx file!')">
          ⬇️ Download Formatted Thesis (.docx)
        </a>
      </div>

    </div>
  </div>

  <script>
    const pages = [
      "{p1}",
      "{p2}",
      "{p3}"
    ];

    function toggleCustomMode(val) {{
      document.getElementById('customBox').style.display = (val === 'custom') ? 'block' : 'none';
      const sel = document.getElementById('universitySelect');
      document.getElementById('modalUnivName').innerText = sel.options[sel.selectedIndex].text + ' • 5 Pages';
    }}

    function loadSampleDoc() {{
      document.getElementById('fileTitle').innerText = 'Sample_AAU_MSc_Thesis.docx';
      document.getElementById('fileDesc').innerText = '✓ Ready for formatting (38.8 KB • 5 Pages)';
    }}

    function openPreviewModal() {{
      document.getElementById('previewModal').style.display = 'flex';
      showPage(0);
    }}

    function closePreviewModal() {{
      document.getElementById('previewModal').style.display = 'none';
    }}

    function showPage(idx) {{
      document.getElementById('mainPageImg').src = pages[idx];
      for (let i = 0; i < 3; i++) {{
        document.getElementById('tab' + i).className = (i === idx) ? 'tab-btn active' : 'tab-btn';
      }}
    }}

    function openCheckout() {{
      document.getElementById('paywallContainer').style.display = 'none';
      document.getElementById('checkoutBox').style.display = 'block';
    }}

    function simulatePayment() {{
      document.getElementById('checkoutBox').style.display = 'none';
      document.getElementById('successBox').style.display = 'block';
    }}
  </script>

</body>
</html>
"""

with open('/home/user/ETHIOFORMAT_PREVIEW.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Saved /home/user/ETHIOFORMAT_PREVIEW.html successfully!")

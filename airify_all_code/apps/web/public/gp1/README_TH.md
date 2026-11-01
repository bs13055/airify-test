# Airify GP1 / Try Airify Now

This is an educational prototype added under `airify_all_code/apps/web/public/gp1/` in the existing Airify repository. The landing page, interactive air-quality explorer, and team page are separate routes:

- `index.html` — Airify Startup Landing Page
- `try.html` — Thailand air-quality explorer and personal exposure scenario calculator
- `about.html` — startup overview and four team members with photos and resume links

## Run locally

From `airify_all_code/apps/web/`, run `npm ci` once and `npm run dev`. Open `/gp1/` in the browser. To test the GitHub Pages base path, run `npm run build -- --mode github-pages`, then `npm run preview -- --mode github-pages` and open `/Airify/gp1/`.

The Landing and About pages use the locally bundled Bootstrap 5.3.3 CSS, responsive grid, navbar collapse component, and JavaScript bundle. Try Airify Now uses a custom responsive dashboard based on the original Airify Health screens.

## Data and privacy

The site calls the public Open-Meteo Geocoding, Air Quality, and Forecast APIs from the browser. PM2.5 and AQI are **model estimates**, not measurements from a nearby street sensor or the user. CAMS Global forecasts have about 45 km spatial resolution and 3-hour time resolution; Open-Meteo may automatically combine supported domains. Every result shows its source and model nature. Current readings, maps, historical charts and exposure inputs use Open-Meteo only on mobile and desktop, with no demo data source. The user-authorized seven-day future daily forecast is the explicit exception: provider, mixed and experimental Airify values are labeled separately, as described below. If requests fail or return no PM2.5 value, the site shows an error and no made-up current value. Existing browser preferences migrate to the external source while names, pins, and other preferences are retained. Prior sample exposure records remain stored but do not appear in the displayed history. Mobile readings include the provider reference time in Thailand time.

Geolocation is requested only after the user presses the location button. The selected coordinates are sent to Open-Meteo to retrieve data. The demo has no login or backend; saved exposure scenarios stay in browser `localStorage`, with a clear-history control.

The exposure estimate uses `C × breathing-rate assumption × hours × environment factor × mask factor` and reports an estimated inhaled mass in µg. The assumptions are illustrative, not clinically validated; this is not lung deposition, individual risk assessment, diagnosis, or medical advice. The comparison bar is a heuristic scenario comparison, not a health or safety threshold.

Open-Meteo's free API is restricted to non-commercial use and attribution, with published request limits. This classroom preview is for non-commercial educational use. A commercial product or promotional deployment would need a suitable licence. Sources: [Air Quality API](https://open-meteo.com/en/docs/air-quality-api), [Geocoding API](https://open-meteo.com/en/docs/geocoding-api), [Terms](https://open-meteo.com/en/terms). Credit Open-Meteo and CAMS/Copernicus in downstream use.

Leaflet and OpenStreetMap are loaded from their public services and are credited on the map. The map plots model readings for 16 reference cities plus the selected coordinate; these discrete points are not a continuous PM2.5 heat map. Saved pins retain their real geographical coordinates and fetch model readings for those coordinates. New browsers start without invented home/work/school locations. See [Leaflet](https://leafletjs.com/) and [OpenStreetMap tile usage](https://operations.osmfoundation.org/policies/tiles/).

## มือถือ: ภาพอ้างอิง 24 ตุลาคม 2026

- `/Airify/gp1/try.html?mobile=1#today` เปิด UI มือถือในหน้าต่างพรีวิวกว้างได้ด้วย ส่วนมือถือจริงใช้ `try.html` ตามปกติ
- วันนี้ / พื้นที่ / ประวัติ / บัญชี เป็นแท็บที่ใช้งานได้จริง มีเมนูด้านล่างคงที่และ hash route ของแต่ละแท็บ
- เปลี่ยนกิจกรรมและเวลาเพื่อประเมินใหม่ บันทึกสถานการณ์เอง แล้วเปิดรายละเอียดหรือลบรายการที่บันทึกได้ ประวัติแสดงเฉพาะสถานการณ์ที่บันทึกจากข้อมูล Open-Meteo ไม่รวมรายการสาธิตเดิม
- เลือกพื้นที่จากรายการหรือบริการค้นหาได้ ในแท็บพื้นที่กด “ปักหมุดสถานที่ใหม่” แล้วแตะพิกัดบนแผนที่ หรือลากหมุดเพื่อปรับจุด ตั้งชื่อและบันทึกได้สูงสุด 8 หมุด เก็บไว้ในเบราว์เซอร์เครื่องนี้และยังอยู่หลังรีเฟรช
- หมุดที่บันทึกแสดงเป็นสีน้ำเงินบนแผนที่ เปิดรายละเอียดได้จากหมุดหรือรายการ เปลี่ยนชื่อผ่าน “จัดการ” และลบด้วยปุ่มถังขยะพร้อมยืนยัน หมุดจะหายจากทั้งรายการและแผนที่ สถานที่เดิมยังเก็บไว้
- แผนที่เริ่มจากพื้นที่ที่เลือก กด “ตำแหน่งของฉัน” และอนุญาตสิทธิ์ก่อนจึงใช้ตำแหน่งจากอุปกรณ์ผ่านเบราว์เซอร์ ไม่เปิด GPS อัตโนมัติหรือเฝ้าติดตามต่อเนื่อง บนคอมพิวเตอร์จะเป็นตำแหน่งคอมพิวเตอร์ ไม่ใช่มือถือ
- พิกัดหมุดเป็นตำแหน่งทางภูมิศาสตร์จริง ส่วนค่าฝุ่นมาจากแบบจำลอง Open-Meteo / CAMS กด “ดูค่าฝุ่นจากข้อมูลภายนอก” ในรายละเอียดหมุดเพื่อเลือกพื้นที่นั้นและโหลดค่า ไม่มีโหมดสาธิตหรือค่าฝุ่นที่สร้างขึ้นเอง เมื่อ API ส่งข้อมูลไม่สำเร็จจะแสดงว่าไม่มีข้อมูลพร้อมปุ่มลองใหม่
- โหมดมืด ภาษาไทย/อังกฤษ ชื่อบัญชีตัวอย่าง และตัวเลือกความเป็นส่วนตัวเก็บในเครื่อง ปุ่มออกจากบัญชีตัวอย่างเปลี่ยนเป็นผู้เยี่ยมชม ไม่มีการอ้างว่าเข้าสู่ระบบออนไลน์
- ตัวเลือกแบ่งปันข้อมูลเป็นเพียงการตั้งค่าสาธิต ไม่มีการส่ง analytics ออกจากเครื่อง การปิดตัวเลือกตำแหน่งในแอปไม่เพิกถอนสิทธิ์ geolocation ของเบราว์เซอร์
- ค่าประเมินยังใช้สมมติฐานอัตราหายใจเดิม เช่น เดินทั่วไป 1.2 m³/ชั่วโมง จึงอาจต่างจากตัวเลขในภาพ การเทียบกับนั่งพักไม่ใช่ระดับความเสี่ยงสุขภาพ
- ข้อมูลกราฟย้อนหลังภายนอกใช้ `past_days=30` ตาม [เอกสาร Air Quality API](https://open-meteo.com/en/docs/air-quality-api) แล้วเลือกช่วงแสดงผล 7/30 วัน ไม่เติมค่าที่ผู้ให้บริการไม่ส่งกลับ
- ใช้ `assets/mobile.css` และ `assets/mobile.js` เป็นชั้นนำเสนอมือถือร่วมกับ engine เดิมใน `try.js` หน้า landing และเลย์เอาต์คอม/iPad ใช้โค้ดเดิม

## พยากรณ์ล่วงหน้า 7 วันแบบผสม — เพิ่มตามคำขอผู้ใช้

- ในแท็บวันนี้ ใต้ค่าฝุ่นปัจจุบัน มีค่าเฉลี่ย PM2.5 รายวัน 7 วัน เริ่มพรุ่งนี้ หน้าเดสก์ท็อปใช้ส่วนพยากรณ์เดียวกันแทนรายการ 3 วันเดิม
- ดึง `forecast_days=7` จาก Open-Meteo ซึ่งนับรวมวันนี้ วันที่ API ให้ครบ 24 ชั่วโมงใช้ค่าเฉลี่ยจากผู้ให้บริการโดยตรง และติดป้าย Open-Meteo
- วันสุดท้ายที่มีข้อมูลบางส่วนอย่างน้อย 12 ชั่วโมง และต่อจากวันข้อมูลครบ จะเติมชั่วโมงที่ขาดจากรูปแบบเวลาเดียวกันของวันก่อน ปรับสัดส่วนตามค่าเฉลี่ยชั่วโมงที่ทับซ้อน ป้ายระบุ Open-Meteo + Airify พร้อมจำนวนชั่วโมงจากแต่ละแหล่ง
- วันที่เหลือใช้แนวโน้มค่าเฉลี่ย 3 วันล่าสุดที่ต่อเนื่องกัน โดยลดแรงแนวโน้มวันละ 20% (`phi=0.8`) และจำกัดไม่ให้ค่าติดลบ ป้ายระบุ Airify · ทดลอง ไม่มีการสุ่มตัวเลข
- สูตรเป็นการทดลอง ยังไม่ผ่านการประเมินความแม่นยำกับสถานีตรวจวัด ไม่รวมตัวแปรฝน ลม แหล่งกำเนิดฝุ่น หรือไฟไหม้อย่างชัดเจน ค่าที่คำนวณต่อไม่ถูกนำไปแทนค่าปัจจุบัน กราฟย้อนหลัง จุดแผนที่ หรือผลประเมินการรับฝุ่น
- ถ้าข้อมูลขาดมากเกินไป จุดอ้างอิงไม่ต่อเนื่อง หรือเก่าเกินวันปัจจุบัน จะแสดงว่าไม่มีข้อมูล กดแต่ละวันหรือเมนูวิธีคำนวณเพื่ออ่านรายละเอียดได้ และใช้คีย์บอร์ดกับ native disclosure ได้
- ตรรกะและ UI ใช้ไฟล์ร่วม `assets/forecast-seven.js` และ `assets/forecast-seven.css` ไม่มีระบบ AI ที่ผ่านการฝึกหรือการรับรองความแม่นยำอยู่เบื้องหลัง

## Visual asset provenance

`assets/airify-bangkok-dusk.png` is an AI-generated blue-hour Bangkok skyline background made with OpenAI ImageGen for the Landing hero. Prompt: “Create a wide 16:9 photorealistic website hero background for Airify, a Thai public air-quality awareness platform. Show a modern Bangkok skyline at blue hour, viewed from a rooftop across the city, with layered low-rise and high-rise buildings at a humid distant horizon, subtle warm window lights and deep navy/cobalt atmosphere. Composition: left half dark calm negative space for white headline and buttons; brighter city silhouette across center-right and lower third, visible behind a translucent UI card. Editorial, natural photographic lighting, restrained blue color grade, no smoke or pollution haze, no people, no text, no logos, no charts, no UI, no awkward crops. Intended as an understated landing page background, horizontal.”

## Team data

`assets/team.js` contains four confirmed names, roles, supplied photos and resume URLs for Thaksin, Luksanut, Tanawat and Naphat.

## ช่องทางติดต่อและการตรวจสอบ

- หน้าแรกมี Instagram, Facebook, LINE และเบอร์โทรตามที่ผู้ใช้กำหนด
- รัน `node scripts/check-gp1.cjs` จากโฟลเดอร์เว็บ เพื่อตรวจไฟล์ ลิงก์ภายใน และการจัดการข้อผิดพลาดก่อน build; GitHub Actions รันชุดตรวจนี้ก่อนเผยแพร่ด้วย
- ตรวจเบราว์เซอร์ที่ขนาด 390, 820 และ 1440 พิกเซลแล้ว การทดสอบขนาดจอไม่ใช่การทดสอบทุกอุปกรณ์จริง
- งานนี้เป็น static frontend: ไม่มีระบบชำระเงิน บัญชีออนไลน์ หรือออก API Key
- เมื่อ workflow สำเร็จ ลิงก์หลัก `https://bs13055.github.io/Airify/` เปิดหน้าโครงงานที่ `/Airify/gp1/` โดยแอป React เดิมยังเปิดได้ที่ `/Airify/platform.html`

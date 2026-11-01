# คู่มืออัปโหลด Airify ขึ้น GitHub (Windows)

**ก่อนเผยแพร่:** โค้ดต้นฉบับมีการระบุ `LicenseRef-Proprietary` ต้องได้รับอนุญาตจากผู้มีสิทธิ์เผยแพร่ก่อน และตรวจความลับของไฟล์ที่คัดลอกอีกครั้ง

1. แตก ZIP `Airify-GitHub-Ready.zip` ลง Desktop จะได้โฟลเดอร์ `Airify-GitHub-Ready` ที่เป็นชุดใหม่ (ห้ามแตกทับโปรเจกต์ของเพื่อน)
2. เข้าโฟลเดอร์ `Airify-GitHub-Ready` แล้วคลิกขวา > Open in Terminal
3. รันคำสั่งด้านล่างทีละบรรทัด (ต้องมี Git และเข้าสู่ระบบ GitHub ที่มีสิทธิ์เขียน repo)

```powershell
git init -b main
git remote add origin https://github.com/bs13055/airify-test.git
git add .
git status --short
# ตรวจสอบรายชื่อไฟล์ก่อนเผยแพร่
# หลังยืนยันสิทธิ์และข้อมูลทั้งหมดแล้ว ค่อยรัน:
git commit -m "Import Airify source and GitHub Pages workflow"
git push -u origin main
```

4. ไปที่ https://github.com/bs13055/airify-test/settings/pages เลือก **Build and deployment > Source > GitHub Actions**
5. ดูผลที่ https://github.com/bs13055/airify-test/actions
6. หาก Deployment สำเร็จ เปิด https://bs13055.github.io/airify-test/#/developers

## ข้อจำกัด API

GitHub Pages รันได้เฉพาะเว็บแบบ Static (React ที่ Build แล้ว) — จะไม่รัน Python API
หากต้องการ API ให้โฮสต์ FastAPI แยก แล้วตั้งตัวแปรใน GitHub > Settings > Secrets and variables > Actions > Variables ชื่อ `AIRIFY_API_BASE_URL` มีค่าเป็น origin ของ API เช่น `https://your-api.example` และตั้งค่า CORS ที่ Backend รองรับ `https://bs13055.github.io` ด้วย จากนั้นกด Re-run workflow หรือ push ใหม่

**ต้นฉบับ:** ไฟล์ใน ZIP นี้เตรียมจากสำเนาเท่านั้น ไม่ได้เปลี่ยนโฟลเดอร์ของเพื่อนหรือเว็บไซต์ Vercel เดิม

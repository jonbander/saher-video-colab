# ساهر — مختبر توليد الصور

مشروع عربي أولي يحوّل وصفاً نصياً إلى صورة عبر ComfyUI على GPU. يتكون من واجهة عربية، وAPI صغير لإرسال المهمة ومتابعتها، ومحول قابل لإعادة الاستخدام مع ComfyUI. هذه نسخة تجريبية وليست خدمة إنتاجية أو خدمة توليد غير محدودة.

## التغيير من الفيديو إلى الصور

أرشفت دفاتر الفيديو السابقة تحت `archive/` للاحتفاظ بها، وأصبح المسار الأساسي للمشروع هو **توليد الصور**. يستخدم ملف workflow المضمن نموذج Stable Diffusion 1.5 بدقة 512×512 و16 خطوة، وهذا خيار أخف من نماذج الفيديو وأسهل لتجربة GPU المجانية، لكنه أقدم وجودته أقل من النماذج الأحدث.

لا يضيف Saher قائمة حظر كلمات خاصة بالتطبيق؛ يمرر prompt إلى ComfyUI بعد التحقق التقني من الطول وإزالة الفراغات الطرفية. **لا يمكن ضمان أن النموذج أو المضيف سيقبل كل طلب**، كما تبقى شروط النموذج والمنصة والقوانين سارية. ملف checkpoint الافتراضي موسوم برخصة CreativeML OpenRAIL-M؛ راجع [مصفوفة التراخيص](docs/licenses-ar.md).

## تجربة Kaggle

نزّل [دفتر Saher الخاص بـKaggle](Saher_Kaggle_Image_Demo.ipynb)، واستورده إلى Kaggle Notebook. فعّل Internet وGPU من إعدادات الدفتر وشغّل الخلايا بالترتيب. عدّل `PROMPT` في خلية التوليد؛ تظهر الصورة ورابط تنزيلها داخل الدفتر. لا يفتح الدفتر صفحة ويب أو Tunnel. قد لا يكون GPU متاحاً عند الطلب، وملفات الجلسة مؤقتة. راجع [دليل Kaggle](docs/kaggle-image-ar.md).

## تشغيل واجهة الويب محلياً

يتطلب Python 3.10 أو أحدث وComfyUI مع checkpoint موجود في `ComfyUI/models/checkpoints/`. من جذر هذا المستودع:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export COMFYUI_BASE_URL=http://127.0.0.1:8188
export COMFYUI_WORKFLOW_PATH="$PWD/workflows/sd15-image-api.json"
export COMFYUI_PROMPT_NODE_ID=6
export COMFYUI_PROMPT_INPUT=text
uvicorn saher_image.app:app --host 127.0.0.1 --port 8000
```

بعدها افتح `http://127.0.0.1:8000` على الجهاز نفسه. workflow الافتراضي يقرأ `v1-5-pruned-emaonly-fp16.safetensors` ويحفظ صورة PNG. مرّر prompts كما تريد ضمن 3–4000 محرف؛ التطبيق لا يضيف قائمة حظر محتوى.

## API

- `POST /api/v1/jobs` بجسم JSON يحتوي `prompt`.
- `GET /api/v1/jobs/{job_id}` لمتابعة الطابور والمخرجات.
- `GET /api/v1/jobs/{job_id}/outputs/{output_index}` لاسترجاع ملف الصورة.
- `GET /health` للتحقق من التطبيق.

## الاختبارات والحدود

شغّل `pytest` للاختبارات التي لا تحتاج GPU. لم يُنفذ توليد حقيقي في بيئة التطوير؛ يلزم تشغيل دفتر Kaggle أو ComfyUI محلياً للتأكد من توافق نموذج GPU لديك.

لا يوجد تسجيل دخول، أو حد معدل، أو عزل مستخدمين، أو رفع صور، أو إدارة مهام دائمة. لا تكشف API أو ComfyUI على الإنترنت العام من دون مصادقة وضوابط موارد وملفات. لا تستخدم صور أشخاص دون إذن. لا يمكن للمشروع ضمان توليد كل طلب أو تجاوز شروط النموذج والبيئة المستضيفة.

## ملفات المشروع

- `saher_image/`: واجهة API والعقود ومحول ComfyUI.
- `web/static/index.html`: واجهة عربية متجاوبة لطلب الصور ومعاينتها.
- `workflows/sd15-image-api.json`: workflow نص-إلى-صورة افتراضي.
- `Saher_Kaggle_Image_Demo.ipynb`: دفتر تفاعلي لتوليد صورة من Kaggle.
- `archive/`: تجارب وأدلة الفيديو القديمة المحفوظة للرجوع.

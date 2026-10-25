# البدء السريع — Saher Image

## 1. تثبيت النموذج في ComfyUI

شغّل ComfyUI على خادم GPU خاص. نزّل checkpoint متوافقاً مع شروطه إلى `ComfyUI/models/checkpoints/`، ثم شغّل ComfyUI على عنوان يمكن لتطبيق Saher الوصول إليه. لا تفتح لوحة ComfyUI أو API مباشرة على الإنترنت العام.

للنسخة السريعة على Kaggle، يستخدم الدفتر النموذج الرسمي Stable Diffusion 1.5 FP16 باسم `v1-5-pruned-emaonly-fp16.safetensors`، صورة 512×512، و16 خطوة. هذا النموذج أخف من مسار الفيديو السابق لكنه أقدم وأقل جودة من نماذج أحدث. اقرأ [مصفوفة التراخيص](licenses-ar.md) قبل اختيار نموذج آخر.

## 2. تثبيت Saher وتشغيله

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

افتح `http://127.0.0.1:8000` على الجهاز نفسه. يرسل التطبيق النص إلى عقدة prompt في workflow المحدد، ويتابع المهمة، ثم يعرض الصورة. لا يضيف Saher قائمة حظر كلمات مخصصة؛ لكن لا يمكن ضمان أن النموذج أو الخدمة ستنتج كل طلب. تبقى شروط النموذج والمنصة والقوانين واجبة.

## 3. تجربة Kaggle

نزّل [دفتر Saher لكاغل](../Saher_Kaggle_Image_Demo.ipynb)، واستورده إلى Kaggle Notebook. فعّل Internet وGPU، وشغّل الخلايا بالترتيب. غيّر متغير `PROMPT` ثم شغّل خلية التوليد. النتيجة ورابط تنزيلها يظهران داخل الدفتر؛ لا تُفتح صفحة ويب مستقلة. التفاصيل في [دليل Kaggle](kaggle-image-ar.md).

## استكشاف الأعطال

- إذا ظهرت `503`، تحقق من مسار workflow وأنه موجود.
- إذا رفض ComfyUI المهمة، تحقق من تثبيت checkpoint الصحيح، وحداثة عقد ComfyUI الافتراضية، ومن صحة JSON API.
- إذا تعذر الاتصال بالمحرك، تحقق من `COMFYUI_BASE_URL` والاتصال الشبكي.
- إذا اكتملت المهمة من دون صورة، تحقق من وجود عقدة `SaveImage` ومخرجاتها في ComfyUI.
- في Kaggle، افحص `/kaggle/working/comfyui.log` عند خروج المحرك، وتحقق من Internet وGPU. الموارد المجانية غير مضمونة.

## حدود النشر والسلامة

هذا النموذج الأولي بلا تسجيل دخول أو عزل للمستخدمين، لذلك لا تنشره كخدمة عامة دون إضافة المصادقة والحصص وضوابط الرفع والمخرجات. لا تدخل بيانات شخصية أو صور أشخاص دون إذن. قد يرفض النموذج أو المضيف بعض الطلبات، ويجب استخدام النموذج وفق رخصته.

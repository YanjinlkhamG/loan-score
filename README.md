# ЗээлСкор — Loan Scoring Web App

## Суулгах
```bash
pip install -r requirements.txt
```

## Ажиллуулах
```bash
# loan_scoring_model.pkl файлыг app.py-тай нэг хавтсанд байрлуул
python app.py
# http://localhost:5000 хаягаар нээнэ
```

## Файлын бүтэц
```
loan_app/
  app.py                    ← Flask backend
  loan_scoring_model.pkl    ← Таны модель (хуулна уу)
  templates/
    index.html              ← UI
  requirements.txt
```

## Скорын тайлбар
| Скор | Шийдвэр |
|------|---------|
| 700–1000 | Зөвшөөрөх |
| 450–699  | Гар шалгалт |
| 0–449    | Татгалзах |

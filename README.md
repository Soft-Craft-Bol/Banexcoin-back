-- backend/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── uploads.py
│   │   │   ├── reconciliation.py
│   │   │   ├── wallets.py
│   │   │   └── reports.py
│   │   │
│   │   └── deps.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── wallet.py
│   │   ├── upload.py
│   │   └── reconciliation.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── transaction.py
│   │   └── reconciliation.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── reconciliation_service.py
│   │   ├── excel_service.py
│   │   ├── crypto_service.py
│   │   └── report_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── transaction_repository.py
│   │   └── reconciliation_repository.py
│   │
│   ├── utils/
│   │   ├── excel_parser.py
│   │   ├── validators.py
│   │   └── helpers.py
│   │
│   ├── uploads/
│   │
│   ├── main.py
│
├── alembic/
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
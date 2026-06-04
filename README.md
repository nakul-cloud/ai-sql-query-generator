# AI-Powered SQL Server Query Generator 🚀

An elegant, modern multi-page Streamlit application that uses Google Gemini (Gemini 2.5 Flash) to translate natural language prompts into valid Transact-SQL (T-SQL) queries. The app connects directly to your SQL Server database to extract schemas, execute the generated queries, show the outputs, and allow downloading the result set as CSV.

Additionally, the app features a built-in CSV Uploader page to easily load data files straight into SQL Server.

## 🛠️ Project Structure

```text
d:\ai-sql-query-generator\
├── .env                       # Environment variables config (DB connection & Gemini API key)
├── app.py                     # Main dashboard, prompt input, AI generator & SQL executor
├── database/
│   └── sql_server.py          # SQL Server connection logic, schema extraction & execution helpers
├── pages/
│   └── upload.py              # File uploader interface to load CSVs into database tables
├── utils/
│   └── csv_processor.py       # Helper functions to read CSVs and upload via SQLAlchemy
└── venv/                      # Local Python Virtual Environment
```

## 📋 Prerequisites

1. **Microsoft SQL Server**: A running SQL Server instance (local or remote).
2. **SQL Server ODBC Driver**: Ensure you have `ODBC Driver 17 for SQL Server` (or similar) installed on your system. You can verify or download it from Microsoft's website.
3. **Google Gemini API Key**: Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).

## ⚙️ Setup & Configuration

1. **Activate the Virtual Environment**:
   ```powershell
   .\venv\Scripts\activate
   ```

2. **Configure Environment Variables**:
   Open the `.env` file in the root directory and configure it to match your database settings:
   ```env
   # SQL Server Connection Configurations
   DB_SERVER=localhost
   DB_DATABASE=YourDatabaseName
   DB_DRIVER=ODBC Driver 17 for SQL Server
   DB_TRUSTED_CONNECTION=yes # Set to yes if using Windows Authentication, else no
   DB_USERNAME=              # Leave blank if using Windows Auth
   DB_PASSWORD=              # Leave blank if using Windows Auth
   DB_ENCRYPT=no
   DB_TRUST_SERVER_CERTIFICATE=yes

   # Google Gemini API Configuration
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

## 🚀 Running the Application

To start the Streamlit development server:

```bash
.\venv\Scripts\streamlit run app.py
```

The application will start, and a browser window should open automatically at `http://localhost:8501`.

## 💡 How to Use

1. **Upload Data** (Optional):
   - Navigate to the **Upload Data** tab in the sidebar.
   - Upload any CSV file.
   - View the dataset preview.
   - Enter a target table name or select an existing table to append data, then click **Upload to Database**.

2. **Generate SQL Queries**:
   - Return to the **app** page.
   - Check the **Connections & Metadata** panel in the sidebar to verify your SQL Server database status is **Connected** and Gemini status is **Active**.
   - Review your database schemas in the sidebar explorer.
   - Write your query in plain English (e.g. *"Show me the total number of sales for each product, ordered by total sales descending"*).
   - Click **Generate SQL Query**.
   - Edit the generated SQL directly in the editor canvas if desired.
   - Click **Run Query** to execute, view the visual table output, and download the data as CSV.

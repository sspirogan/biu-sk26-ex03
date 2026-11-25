<div dir="rtl">

<h1>מסמך דרישות מוצר (<bdi dir="ltr">PRD</bdi>) — שרת <bdi dir="ltr">MCP</bdi> עבור <bdi dir="ltr">Gmail</bdi> ו-<bdi dir="ltr">Google Calendar</bdi></h1>

<p>מסמך זה מתאר את הפרויקט הקיים <code dir="ltr">gmail-calendar</code> במטלה <bdi dir="ltr">03</bdi> (<bdi dir="ltr">L06</bdi>) כפי שהוא ממומש ומתועד במאגר הנוכחי, בלי להוסיף יכולות או תוצאות שלא אומתו.</p>

<h2><bdi dir="ltr">1.</bdi> בעיה ומטרה</h2>

<h3>הבעיה</h3>
<p>תיאום פגישות דרך הדואר האלקטרוני והיומן דורש מעבר ידני בין חיפוש הודעות, בדיקת זמינות בשעות העבודה המקומיות, יצירת אירוע חדש וניסוח מענה לשולח. מנגד, חיבור של מודל שפה גדול (<bdi dir="ltr">LLM</bdi>) לחשבון <bdi dir="ltr">Google</bdi> ללא מגבלות קשיחות עלול להוביל לפעולות בלתי הפיכות או מסוכנות, כגון שליחת הודעות בשם המשתמש או מחיקת מיילים ואירועים.</p>

<h3>המטרה</h3>
<p>לאפשר שימוש ב-<bdi dir="ltr">LLM</bdi> באמצעות פרוטוקול <bdi dir="ltr">MCP</bdi> (<bdi dir="ltr">Model Context Protocol</bdi>) מול שרת מקומי בשם <code dir="ltr">gmail-calendar</code>, כדי לקרוא הודעות ב-<bdi dir="ltr">Gmail</bdi>, לבדוק זמינות וליצור אירועים ב-<bdi dir="ltr">Google Calendar</bdi>, ולהכין טיוטת תגובה (<bdi dir="ltr">draft</bdi>) ב-<bdi dir="ltr">Gmail</bdi> — תוך שמירה על בקרה אנושית מלאה וללא יכולת שליחה או מחיקה.</p>

<h2><bdi dir="ltr">2.</bdi> משתמשי היעד ותהליך העבודה העיקרי</h2>

<h3>משתמשי היעד</h3>
<ul>
  <li>משתמש קצה או סטודנט בקורס המפעיל לקוח <bdi dir="ltr">MCP</bdi> תומך (כגון <bdi dir="ltr">Claude Desktop</bdi>, <bdi dir="ltr">Cursor</bdi> או <bdi dir="ltr">Antigravity</bdi>) המחובר לשרת <code dir="ltr">gmail-calendar</code>.</li>
  <li>בעל החשבון ב-<bdi dir="ltr">Google</bdi> המבקש להיעזר בסוכן לתיאום פגישות, תוך השארת השליחה הסופית של הודעות והמחיקה של נתונים בידי האדם.</li>
</ul>

<h3>תהליך העבודה העיקרי (תיאום פגישה)</h3>
<ol>
  <li>המשתמש מזין בקשה בשפה טבעית ללקוח ה-<bdi dir="ltr">MCP</bdi> (למשל, טיפול בבקשת פגישה שהתקבלה במייל).</li>
  <li>המודל מאתר את ההודעה הרלוונטית באמצעות <code dir="ltr">search_emails</code> וקורא את תוכנה המלא באמצעות <code dir="ltr">read_email</code> (תוך התייחסות לתוכן המייל כנתונים בלבד ולא כהוראות הפעלה).</li>
  <li>המודל בודק זמינות ביומן הראשי באזור הזמן <code dir="ltr">Asia/Jerusalem</code> באמצעות <code dir="ltr">list_events</code> ו/או <code dir="ltr">find_free_slots</code>, ובמידת הצורך מוודא שלא קיים כבר אירוע כפול.</li>
  <li>אם השעה המבוקשת פנויה: המודל יוצר אירוע ביומן באמצעות <code dir="ltr">create_event</code> ומכין טיוטת אישור לשולח באמצעות <code dir="ltr">create_draft</code>.</li>
  <li>אם השעה תפוסה: המודל אינו יוצר אירוע, אלא מכין טיוטת תשובה בלבד עם חלופות זמינות באמצעות <code dir="ltr">create_draft</code>.</li>
  <li>המשתמש סוקר ידנית את הטיוטה ב-<bdi dir="ltr">Gmail</bdi> ואת האירוע ב-<bdi dir="ltr">Google Calendar</bdi>, ומחליט בעצמו אם לשלוח את המייל.</li>
</ol>

<h2><bdi dir="ltr">3.</bdi> ששת הכלים הקיימים, קלטים ותוצאות צפויות</h2>

<p>השרת מוגדר בקובץ <code dir="ltr">src/gmail_calendar/server.py</code> וחושף בדיוק שישה כלים (<bdi dir="ltr">MCP tools</bdi>):</p>

<table dir="rtl">
  <thead>
    <tr>
      <th>שם הכלי</th>
      <th>קלטים (<bdi dir="ltr">Parameters</bdi>)</th>
      <th>פעולת <bdi dir="ltr">API</bdi> ואימותים</th>
      <th>תוצאה צפויה (<bdi dir="ltr">Output</bdi>)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code dir="ltr">search_emails</code></td>
      <td>
        <code dir="ltr">query: str</code><br>
        <code dir="ltr">max_results: int = 10</code>
      </td>
      <td>
        בודק ש-<code dir="ltr">1 &lt;= max_results &lt;= 100</code>. קורא ל-<code dir="ltr">users().messages().list</code> בתחביר החיפוש של <bdi dir="ltr">Gmail</bdi> ול-<code dir="ltr">users().messages().get</code> (<code dir="ltr">format="metadata"</code>) לכותרות <code dir="ltr">From</code>, <code dir="ltr">To</code>, <code dir="ltr">Subject</code>, <code dir="ltr">Date</code>.
      </td>
      <td>
        מילון הכולל <code dir="ltr">query</code>, <code dir="ltr">count</code> ורשימת <code dir="ltr">emails</code> (לכל הודעה: <code dir="ltr">id</code>, <code dir="ltr">thread_id</code>, <code dir="ltr">from</code>, <code dir="ltr">to</code>, <code dir="ltr">subject</code>, <code dir="ltr">date</code>, <code dir="ltr">snippet</code>).
      </td>
    </tr>
    <tr>
      <td><code dir="ltr">read_email</code></td>
      <td><code dir="ltr">message_id: str</code></td>
      <td>
        מוודא ש-<code dir="ltr">message_id</code> אינו ריק. קורא ל-<code dir="ltr">users().messages().get</code> עם <code dir="ltr">format="full"</code> ומחלץ גוף טקסט (<code dir="ltr">text/plain</code> או <code dir="ltr">text/html</code> לאחר ניקוי תגיות).
      </td>
      <td>
        מילון הכולל <code dir="ltr">id</code>, <code dir="ltr">thread_id</code>, <code dir="ltr">from</code>, <code dir="ltr">to</code>, <code dir="ltr">cc</code>, <code dir="ltr">subject</code>, <code dir="ltr">date</code>, <code dir="ltr">snippet</code>, <code dir="ltr">body</code> ו-<code dir="ltr">labels</code>.
      </td>
    </tr>
    <tr>
      <td><code dir="ltr">create_draft</code></td>
      <td>
        <code dir="ltr">to: str</code><br>
        <code dir="ltr">subject: str</code><br>
        <code dir="ltr">body: str</code>
      </td>
      <td>
        מוודא ש-<code dir="ltr">to</code> אינו ריק. בונה <code dir="ltr">EmailMessage</code> מקודד ב-<bdi dir="ltr">base64url</bdi> וקורא ל-<code dir="ltr">users().drafts().create</code> בלבד (ללא שליחה).
      </td>
      <td>
        מילון עם <code dir="ltr">status: "draft_created"</code>, <code dir="ltr">draft_id</code>, <code dir="ltr">message_id</code>, <code dir="ltr">to</code> ו-<code dir="ltr">subject</code>.
      </td>
    </tr>
    <tr>
      <td><code dir="ltr">list_events</code></td>
      <td><code dir="ltr">days_ahead: int = 7</code></td>
      <td>
        בודק ש-<code dir="ltr">1 &lt;= days_ahead &lt;= 365</code>. קורא ל-<code dir="ltr">events().list</code> ביומן <code dir="ltr">primary</code> מהזמן הנוכחי ב-<code dir="ltr">Asia/Jerusalem</code> ועד <code dir="ltr">days_ahead</code> ימים קדימה (<code dir="ltr">singleEvents=True</code>, <code dir="ltr">orderBy="startTime"</code>).
      </td>
      <td>
        מילון עם <code dir="ltr">timezone: "Asia/Jerusalem"</code>, <code dir="ltr">from</code>, <code dir="ltr">to</code>, <code dir="ltr">count</code> ורשימת <code dir="ltr">events</code> מנורמלת (<code dir="ltr">id</code>, <code dir="ltr">title</code>, <code dir="ltr">start</code>, <code dir="ltr">end</code>, <code dir="ltr">location</code>, <code dir="ltr">description</code>, <code dir="ltr">status</code>, <code dir="ltr">html_link</code>).
      </td>
    </tr>
    <tr>
      <td><code dir="ltr">find_free_slots</code></td>
      <td>
        <code dir="ltr">date: str</code> (<code dir="ltr">YYYY-MM-DD</code>)<br>
        <code dir="ltr">duration_minutes: int = 30</code>
      </td>
      <td>
        בודק ש-<code dir="ltr">duration_minutes &gt;= 1</code>. שולף אירועים ביומן <code dir="ltr">primary</code> בטווח <code dir="ltr">08:00-20:00</code> לפי <code dir="ltr">Asia/Jerusalem</code>, מדלג על אירועים במצב <code dir="ltr">cancelled</code> או <code dir="ltr">transparent</code> וממזג חפיפות.
      </td>
      <td>
        מילון עם <code dir="ltr">date</code>, <code dir="ltr">timezone: "Asia/Jerusalem"</code>, <code dir="ltr">window: "08:00-20:00"</code>, <code dir="ltr">duration_minutes</code> ורשימת <code dir="ltr">free_slots</code> (<code dir="ltr">start</code>, <code dir="ltr">end</code>, <code dir="ltr">duration_minutes</code>).
      </td>
    </tr>
    <tr>
      <td><code dir="ltr">create_event</code></td>
      <td>
        <code dir="ltr">title: str</code><br>
        <code dir="ltr">start: str</code><br>
        <code dir="ltr">end: str</code><br>
        <code dir="ltr">description: str = ""</code>
      </td>
      <td>
        מוודא ש-<code dir="ltr">title</code> אינו ריק, מפרש מחרוזות <bdi dir="ltr">ISO 8601</bdi> (זמנים ללא אזור זמן מקבלים <code dir="ltr">Asia/Jerusalem</code>), מוודא ש-<code dir="ltr">end &gt; start</code>, וקורא ל-<code dir="ltr">events().insert</code> ביומן <code dir="ltr">primary</code>.
      </td>
      <td>
        מילון עם <code dir="ltr">status: "event_created"</code>, <code dir="ltr">timezone: "Asia/Jerusalem"</code> ו-<code dir="ltr">event</code> המכיל את פרטי האירוע שנוצר.
      </td>
    </tr>
  </tbody>
</table>

<h2><bdi dir="ltr">4.</bdi> דרישות טכניות ואבטחתיות</h2>

<ul>
  <li><strong>תעבורת <code dir="ltr">stdio</code>:</strong> השרת מופעל באמצעות <code dir="ltr">MCPServer("gmail-calendar")</code> מתוך חבילת <code dir="ltr">mcp</code> (גרסה <bdi dir="ltr">2.3.0</bdi> ומעלה) עם <code dir="ltr">mcp.run(transport="stdio")</code>, כדי שלקוח <bdi dir="ltr">MCP</bdi> יתקשר עמו דרך קלט/פלט תקניים.</li>
  <li><strong>ניהול והרצה עם <code dir="ltr">uv</code>:</strong> הפרויקט מוגדר ב-<code dir="ltr">pyproject.toml</code> עבור <bdi dir="ltr">Python 3.13+</bdi> עם <code dir="ltr">uv_build</code> ונקודת הכניסה <code dir="ltr">gmail-calendar = "gmail_calendar:main"</code> (וכן הרצה כמודול <code dir="ltr">python -m gmail_calendar</code>). ההפעלה מתבצעת עם <code dir="ltr">uv sync</code> ו-<code dir="ltr">uv run gmail-calendar</code>.</li>
  <li><strong>אזור זמן <code dir="ltr">Asia/Jerusalem</code>:</strong> קבוע בקובץ <code dir="ltr">src/gmail_calendar/calendar_helpers.py</code> באמצעות <code dir="ltr">ZoneInfo("Asia/Jerusalem")</code>. כל תשאולי היומן, חישובי הזמינות (<code dir="ltr">08:00-20:00</code>) ויצירת האירועים מתבצעים ונשמרים באזור זמן זה.</li>
  <li><strong>טעינת הרשאות מתיקייה חיצונית (<code dir="ltr">GOOGLE_PRIVATE_DIR</code>):</strong> המודול <code dir="ltr">src/gmail_calendar/auth.py</code> קורא את נתיב התיקייה ממשתנה הסביבה <code dir="ltr">GOOGLE_PRIVATE_DIR</code> בלבד, וטוען ממנה את <code dir="ltr">client_secret*.json</code> ואת <code dir="ltr">token.json</code>. אסימונים שפג תוקפם מתרעננים בזיכרון בלבד באמצעות <code dir="ltr">refresh_token</code>, ללא כתיבת קובצי סודות למאגר, ללא הדפסת סודות וללא פתיחת דפדפן מתוך שרת ה-<bdi dir="ltr">MCP</bdi>.</li>
  <li><strong>שמירה על ניקיון המאגר והרשאות נפרדות:</strong> קובץ <code dir="ltr">.gitignore</code> מחריג את <code dir="ltr">token.json</code>, <code dir="ltr">client_secret*.json</code>, <code dir="ltr">credentials.json</code>, <code dir="ltr">.env</code> ו-<code dir="ltr">.venv</code>. הרשאת <bdi dir="ltr">OAuth</bdi> בדפדפן הופרדה לסקריפט העצמאי <code dir="ltr">scripts/authorize_oauth.py</code> המבקש את ההרשאות <code dir="ltr">gmail.readonly</code>, <code dir="ltr">gmail.compose</code> ו-<code dir="ltr">calendar.events</code>.</li>
</ul>

<h2><bdi dir="ltr">5.</bdi> יכולות שהוחרגו במפורש והסיבה לכך</h2>

<ul>
  <li><strong>שליחת מיילים (<code dir="ltr">messages.send</code> / <code dir="ltr">drafts.send</code>):</strong> לא קיים כלי לשליחת מייל או לשליחת טיוטה. כלי הכתיבה היחיד ב-<bdi dir="ltr">Gmail</bdi> הוא <code dir="ltr">create_draft</code>.</li>
  <li><strong>מחיקת מיילים, טיוטות או אירועי יומן:</strong> לא קיים כל כלי למחיקה או להעברה לאשפה ב-<bdi dir="ltr">Gmail</bdi> או ב-<bdi dir="ltr">Google Calendar</bdi>.</li>
  <li><strong>עדכון אירועים קיימים או פתיחת דפדפן מתוך השרת:</strong> השרת אינו חושף כלי לעריכה/מחיקה של אירועים קיימים ואינו מפעיל זרימת התחברות בדפדפן.</li>
</ul>

<p><strong>הסיבה למגבלות:</strong> עקרון הפחתת סיכונים ושליטה אנושית (<bdi dir="ltr">Human-in-the-Loop</bdi>). שליחת דוא"ל לנמען חיצוני או מחיקת מידע ביומן ובתיבת הדואר הן פעולות בעלות השלכות שקשה או בלתי אפשרי לבטל. השארת פעולות אלו מחוץ לכלים החשופים ל-<bdi dir="ltr">LLM</bdi> מצמצמת את הסיכון מטעויות של המודל, אי-הבנות בניסוח הבקשה או תוכן מייל לא מהימן, אך אינה מבטיחה הגנה מלאה מפני כל טעות או מפני <bdi dir="ltr">Prompt Injection</bdi>.</p>

<h2><bdi dir="ltr">6.</bdi> קריטריוני קבלה — דרישות מול תוצאות מאומתות</h2>

<p>יש להבחין בין דרישות הפרויקט לבין מה שנבדק ואומת בפועל:</p>

<h3>דרישות הקבלה של הפרויקט</h3>
<ul>
  <li>חשיפת ששת הכלים המוגדרים בלבד (<code dir="ltr">search_emails</code>, <code dir="ltr">read_email</code>, <code dir="ltr">create_draft</code>, <code dir="ltr">list_events</code>, <code dir="ltr">find_free_slots</code>, <code dir="ltr">create_event</code>) עם תיאור ברור באנגלית, וללא כלי שליחה או מחיקה.</li>
  <li>הפעלה תקינה מעל <code dir="ltr">stdio</code> באמצעות <code dir="ltr">uv</code> ורישום תקין בקובץ תצורת <bdi dir="ltr">MCP</bdi>.</li>
  <li>שימוש עקבי באזור הזמן <code dir="ltr">Asia/Jerusalem</code> וחישוב זמינות בחלון <code dir="ltr">08:00-20:00</code>.</li>
  <li>טעינת אישורים מ-<code dir="ltr">GOOGLE_PRIVATE_DIR</code> מחוץ למאגר, ללא חשיפת סודות או הכללת קובצי הרשאה במאגר.</li>
  <li>מעבר בדיקות היחידה ובדיקת האינטגרציה החיה, וביצוע מלא של תרחיש תיאום פגישה מקצה לקצה עם טיוטה ואירוע מתועדים.</li>
</ul>

<h3>מצב האימות הנוכחי</h3>
<ul>
  <li><strong>אומת בקריאת הקוד והקבצים בסשן הנוכחי (בדיקה סטטית בלבד):</strong>
    <ul>
      <li>קובץ <code dir="ltr">src/gmail_calendar/server.py</code> רושם את ששת הכלים בלבד ומריץ את השרת מעל <code dir="ltr">stdio</code>.</li>
      <li>מימוש הכלים ב-<code dir="ltr">gmail_tools.py</code>, <code dir="ltr">calendar_tools.py</code> ו-<code dir="ltr">calendar_helpers.py</code> אינו כולל קריאות שליחה או מחיקה ומשתמש ב-<code dir="ltr">Asia/Jerusalem</code>.</li>
      <li>קובץ <code dir="ltr">auth.py</code> קורא מ-<code dir="ltr">GOOGLE_PRIVATE_DIR</code> בלבד, ובמאגר אין קובצי <code dir="ltr">token.json</code>, <code dir="ltr">client_secret*.json</code>, <code dir="ltr">credentials.json</code> או <code dir="ltr">.env</code>; קובץ <code dir="ltr">.gitignore</code> מחריג אותם.</li>
      <li>קיימים קובצי בדיקות: <code dir="ltr">tests/test_server.py</code> (בדיקות יחידה עם <code dir="ltr">MagicMock</code> לשכבת ה-<bdi dir="ltr">API</bdi> ובדיקת <bdi dir="ltr">stdio handshake</bdi> על רשימת <bdi dir="ltr">6</bdi> הכלים) ו-<code dir="ltr">test_server.py</code> (סקריפט אינטגרציה לקריאת <code dir="ltr">list_events</code>).</li>
    </ul>
  </li>
  <li><strong>מדווח בתיעוד הקודם במאגר (ללא אימות חוזר בסשן זה):</strong>
    <ul>
      <li>בקובץ <code dir="ltr">README.md</code> ובקובץ <code dir="ltr">reflection.md</code> מתועד כי לאחר תיקון הרשאות <bdi dir="ltr">OAuth</bdi> (<code dir="ltr">gmail.readonly</code>) והפעלת השרת מחדש, בוצע תרחיש תיאום פגישה שבו נוצר אירוע ביומן ל-<bdi dir="ltr">1</bdi> בדצמבר בשעה <bdi dir="ltr">10:00</bdi> למשך <bdi dir="ltr">45</bdi> דקות ונשמרה טיוטת תשובה ללא שליחה, וכי בקשות שליחה ומחיקה סורבו על ידי הסוכן.</li>
    </ul>
  </li>
  <li><strong>לא הורץ ולא אומת בסשן הנוכחי:</strong>
    <ul>
      <li>לא הורצו בדיקות <code dir="ltr">tests/test_server.py</code> או <code dir="ltr">test_server.py</code> בסביבה הנוכחית.</li>
      <li>לא בוצעה התחברות ל-<bdi dir="ltr">Google</bdi>, לא נקראו קובצי האישורים המקומיים ולא אומת חיבור חי ל-<bdi dir="ltr">Gmail</bdi> או ל-<bdi dir="ltr">Google Calendar</bdi>.</li>
      <li>טרם אומתה תצורת ההרצה של לקוח ה-<bdi dir="ltr">MCP</bdi> על גבי מערכת ההפעלה הנוכחית (<bdi dir="ltr">Windows</bdi>).</li>
    </ul>
  </li>
</ul>

<h2><bdi dir="ltr">7.</bdi> מגבלות ידועות</h2>

<ul>
  <li><strong>אי-מימוש דפדוף ביומן (<bdi dir="ltr">Calendar pagination</bdi>):</strong> הפונקציות <code dir="ltr">list_events</code> ו-<code dir="ltr">find_free_slots</code> בקובץ <code dir="ltr">src/gmail_calendar/calendar_tools.py</code> מבצעות קריאה יחידה ל-<code dir="ltr">service.events().list(...).execute()</code> ואינן מטפלות ב-<code dir="ltr">nextPageToken</code>. אם בטווח התאריכים המבוקש יש יותר מעמוד תוצאות אחד, אירועים בעמודים הבאים לא יופיעו בפלט ולא יילקחו בחשבון בחישוב חלונות פנויים.</li>
  <li><strong>נתיבים תלויי-מכונה בתצורת <bdi dir="ltr">MCP</bdi>:</strong> הקובץ <code dir="ltr">.agents/mcp_config.json</code> (וכן דוגמאות בקובץ <code dir="ltr">README.md</code> וברירות המחדל ב-<code dir="ltr">test_server.py</code> וב-<code dir="ltr">scripts/authorize_oauth.py</code>) מכילים נתיבי <bdi dir="ltr">macOS</bdi> קשיחים (<code dir="ltr">/Users/pirogan4ik/Desktop/שיעור 7</code> ו-<code dir="ltr">/Users/pirogan4ik/Desktop/private</code>). תצורה זו אינה פועלת ללא התאמה ידנית של הנתיבים במחשבים אחרים או בסביבת <bdi dir="ltr">Windows</bdi> הנוכחית (<code dir="ltr">C:\BIU01\HW3\biu-sk26-ex03</code>).</li>
  <li><strong>עמידות בפני <bdi dir="ltr">Prompt Injection</bdi> לא נבדקה בנפרד:</strong> הפונקציה <code dir="ltr">read_email</code> מחזירה למודל השפה את גוף המייל הגולמי (או טקסט מחולץ מ-<bdi dir="ltr">HTML</bdi>) ללא סינון או בידוד תוכני בקוד, וההגנה מפני הזרקת הוראות בתוך הודעות נסמכת על התנהגות המודל והנחיות המשתמש בלבד. לא בוצעו בדיקות ייעודיות לבחינת עמידות מפני <bdi dir="ltr">Prompt Injection</bdi>.</li>
  <li><strong>מגבלות מימוש נוספות הנצפות בקוד:</strong> חישוב הזמינות ב-<code dir="ltr">find_free_slots</code> מוגבל לחלון הקבוע <code dir="ltr">08:00-20:00</code> וליומן <code dir="ltr">primary</code> בלבד; האסימון הטעון נשמר במטמון התהליך (<code dir="ltr">_cached_creds</code>), ולכן לאחר רענון ידני של <code dir="ltr">token.json</code> נדרשת הפעלה מחדש של שרת ה-<bdi dir="ltr">MCP</bdi>.</li>
</ul>

<h2><bdi dir="ltr">8.</bdi> ראיות הגשה שעדיין נדרשות</h2>

<p>לצורך השלמת תיעוד ההגשה, עדיין חסרים ונדרשים להטמעה בתוך קובץ <code dir="ltr">README.md</code>:</p>
<ul>
  <li>צילום מסך מתוך <strong><bdi dir="ltr">Gmail</bdi></strong> המציג את הטיוטה שנוצרה באמצעות השרת (בתיקיית הטיוטות, ללא שליחה).</li>
  <li>צילום מסך מתוך <strong><bdi dir="ltr">Google Calendar</bdi></strong> המציג את האירוע שנוצר ביומן עם התאריך, השעה ואזור הזמן המתאימים.</li>
</ul>

</div>

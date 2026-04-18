(() => {
  const storageKey = 'library_ui_lang';
  const defaultLang = 'zh-CN';
  const supportedLangs = ['zh-CN', 'en'];
  const originalTextNodes = new WeakMap();
  const originalAttributes = new WeakMap();
  let originalTitle = null;
  let observer = null;

  const exactTranslations = {
    en: {
      '图书借阅与会员管理系统': 'Library Borrowing and Membership Management System',
      '馆藏检索与读者服务': 'Catalog Search and Reader Services',
      '首页': 'Home',
      '馆藏检索': 'Catalog',
      '读者服务': 'Reader Services',
      '登录/注册': 'Sign In / Register',
      '登录 / 注册': 'Sign In / Register',
      '进入读者服务': 'Open Reader Services',
      '进入管理后台': 'Open Admin Portal',
      '退出登录': 'Sign Out',
      '公告': 'Notice',
      '开放时间提醒': 'Opening Hours Reminder',
      '正在加载最新公告…': 'Loading the latest notice...',
      '欢迎使用图书馆服务。': 'Welcome to the library service.',
      '欢迎使用图书馆服务。借书、还书和预约办理请按页面提示操作。': 'Welcome to the library service. Follow the page guidance for borrowing, returning, and reservations.',
      '统一登录': 'Unified Sign In',
      '读者注册': 'Reader Registration',
      '注册通过审核后可进入读者服务。': 'After approval, you can use Reader Services.',
      '账号登录': 'Account Sign In',
      '邮箱': 'Email',
      '密码': 'Password',
      '姓名': 'Name',
      '手机号': 'Phone Number',
      '可留空': 'Optional',
      '例如 2026-04-15T09:00:00': 'e.g. 2026-04-15T09:00:00',
      '例如 2026-04-15T18:00:00': 'e.g. 2026-04-15T18:00:00',
      '按书名、作者或分类搜索图书': 'Search books by title, author, or category',
      '留空则使用系统默认': 'Leave blank to use the default amount',
      '例如 2': 'e.g. 2',
      '系统自动分配副本时填写': 'Fill this in when the system should assign a copy automatically',
      '指定副本时填写': 'Fill this in to specify a copy manually',
      '有条码时可直接录入': 'Enter directly when you have a barcode',
      '可从下方借阅中列表直接带入': 'This can be filled from the active loan list below',
      '按读者、图书名、条码或编号搜索': 'Search by reader, book title, barcode, or ID',
      '按图书编号筛选馆藏副本，可留空': 'Filter library copies by Book ID, or leave blank',
      '例如 欠费未处理 / 账号异常': 'e.g. unpaid fees / account issue',
      '按邮箱、姓名或角色搜索账号': 'Search accounts by email, name, or role',
      '搜索你现在想借的书': 'Search for the book you want now',
      '例如 东野圭吾 / Tolkien': 'e.g. Higashino / Tolkien',
      '输入图书 ID': 'Enter a Book ID',
      '输入图书编号': 'Enter a Book ID',
      '输入书名、作者或分类关键词': 'Enter a title, author, or category keyword',
      '例如 1': 'e.g. 1',
      '输入书名、作者、分类或编号': 'Enter a title, author, category, or ID',
      '先输入书名、作者、分类或编号': 'Start by entering a title, author, category, or ID',
      '登录并进入系统': 'Sign In',
      '新用户注册': 'Register',
      '已有账号，去登录': 'Already have an account? Sign in',
      '注册账号': 'Create Account',
      '注册成功': 'Registration Successful',
      '先看馆藏': 'Browse Catalog First',
      '返回馆藏检索': 'Back to Catalog',
      '返回读者首页': 'Back to Reader Home',
      '返回图书列表': 'Back to Book List',
      '去登录': 'Go to Sign In',
      '去登录页': 'Go to Sign In',
      '找书': 'Find a Book',
      '读者、馆员和管理员都在这里登录，系统会自动进入对应页面。': 'Readers, librarians, and administrators all sign in here, and the system opens the correct page automatically.',
      '登录后会根据账号身份自动进入读者服务或管理后台，不需要再分别找两个入口。': 'After sign-in, the system opens Reader Services or the Admin Portal automatically based on the account role.',
      '看我的借阅': 'My Loans',
      '先搜一本书，或者直接看推荐': 'Search for a book first, or open recommendations',
      '输入书名、作者、分类关键词来查馆藏；如果暂时没有目标，就点右上角的“查看推荐”。': 'Search the catalog by title, author, or category. If you are not sure what to read, open recommendations.',
      '已按“': 'Filtered by “',
      '筛出相关馆藏。': '” with matching catalog results.',
      '当前没有可展示的馆藏结果。': 'There are no catalog results to show right now.',
      '去后台处理业务': 'Go to Back Office',
      '今天先做什么': 'What do you want to do first?',
      '开始找书': 'Start Searching',
      '从这里直接进入你现在最需要的入口，不用先猜应该点哪里。': 'Jump straight to the task you need now without guessing where to click.',
      '按书名、作者、分类和可借状态快速筛选': 'Filter quickly by title, author, category, and availability.',
      '继续借、看预约、看通知都从这里进入': 'Open renewals, reservations, and notifications here.',
      '审批会员、借还书、罚款、公告都在这里': 'Handle approvals, circulation, fines, and notices here.',
      '现在可直接查看的书': 'Books to Start With',
      '先看一批当前更适合直接下手的馆藏，想继续再进入完整检索页。': 'Start with a short list of books worth checking now, then open the full catalog if needed.',
      '这里是首页精选展示，不是全部结果。想继续找，直接进入完整馆藏检索。': 'This is a curated home-page section, not the full result list. Open the full catalog to continue browsing.',
      '打开完整馆藏检索': 'Open Full Catalog',
      '当前入口': 'Current Access',
      '还没有登录': 'Not Signed In',
      '先找书也可以；如果要借阅、预约或处理后台业务，再进入对应入口。': 'You can browse first. Sign in only when you need to borrow, reserve, or handle back-office work.',
      '借书 / 还书': 'Checkout / Check-in',
      '罚款处理': 'Fine Handling',
      '图书管理': 'Book Management',
      '会员审核': 'Member Review',
      '权限管理': 'Role Management',
      '统计报表': 'Reports',
      '公告管理': 'Notice Management',
      '操作日志': 'Audit Log',
      '提醒策略': 'Reminder Policy',
      '管理工作台': 'Admin Portal',
      '返回管理工作台': 'Back to Admin Portal',
      '刷新数据': 'Refresh',
      '切换账号': 'Switch Account',
      '常用入口': 'Quick Access',
      '当前身份：管理员': 'Current Role: Administrator',
      '当前身份：馆员': 'Current Role: Librarian',
      '处理罚款': 'Handle Fines',
      '管理图书': 'Manage Books',
      '图书列表': 'Book List',
      '保存反馈': 'Save Feedback',
      '保存结果会显示在这里': 'The save result will appear here',
      '书名': 'Title',
      '作者': 'Author',
      '分类': 'Category',
      '出版年份': 'Publication Year',
      '简介': 'Description',
      '破损赔偿': 'Damaged Compensation',
      '遗失赔偿': 'Lost Compensation',
      '图书编号': 'Book ID',
      '馆藏副本': 'Library Copy',
      '馆藏副本编号': 'Copy ID',
      '读者编号': 'Reader ID',
      '账号编号': 'Account ID',
      '借阅编号': 'Loan ID',
      '预约编号': 'Reservation ID',
      '操作者编号': 'Operator ID',
      '条码': 'Barcode',
      '条码：': 'Barcode: ',
      '位置': 'Location',
      '状态': 'Status',
      '可借': 'Available',
      '现在可借': 'Available Now',
      '现在能借': 'Available Now',
      '先放入预约': 'Reserve First',
      '暂时借不到': 'Not Available Right Now',
      '可借数量': 'Available Copies',
      '外借中': 'On Loan',
      '维修中': 'Under Maintenance',
      '已丢失': 'Lost',
      '已下架': 'Removed',
      '已归还': 'Returned',
      '待审核': 'Pending Review',
      '正常': 'Active',
      '全部': 'All',
      '全部分类': 'All Categories',
      '全部状态': 'All Statuses',
      '全部类型': 'All Types',
      '全部图书': 'All Books',
      '打开完整书目页': 'Open Full Book List',
      '搜索你现在想借的书': 'Search for the book you want now',
      '按书名、作者或分类搜索图书': 'Search books by title, author, or category',
      '输入书名、作者、分类或编号': 'Enter a title, author, category, or ID',
      '先输入书名、作者、分类或编号': 'Start by entering a title, author, category, or ID',
      '例如 东野圭吾 / Tolkien': 'e.g. Higashino / Tolkien',
      '输入书名、作者或分类关键词': 'Enter a title, author, or category keyword',
      '可留空': 'Optional',
      '例如 2026-04-15T09:00:00': 'e.g. 2026-04-15T09:00:00',
      '例如 2026-04-15T18:00:00': 'e.g. 2026-04-15T18:00:00',
      '例如 2': 'e.g. 2',
      '系统自动分配副本时填写': 'Fill this in when the system should assign a copy automatically',
      '指定副本时填写': 'Fill this in to specify a copy manually',
      '有条码时可直接录入': 'Enter directly when you have a barcode',
      '可从下方借阅中列表直接带入': 'This can be filled from the active loan list below',
      '按图书编号筛选馆藏副本，可留空': 'Filter library copies by Book ID, or leave blank',
      '例如 欠费未处理 / 账号异常': 'e.g. unpaid fees / account issue',
      '按邮箱、姓名或角色搜索账号': 'Search accounts by email, name, or role',
      '例如 1': 'e.g. 1',
      '状态筛选': 'Status Filter',
      '筛选条件': 'Filters',
      '刷新列表': 'Refresh List',
      '操作类型': 'Action Type',
      '对象类型': 'Object Type',
      '开始时间': 'Start Time',
      '结束时间': 'End Time',
      '查询日志': 'Search Logs',
      '日志结果': 'Audit Results',
      '变更前': 'Before',
      '变更后': 'After',
      '暂无变更内容': 'No change details',
      '罚款列表': 'Fine List',
      '未缴': 'Unpaid',
      '已缴': 'Paid',
      '已减免': 'Waived',
      '标记已缴': 'Mark as Paid',
      '减免罚款': 'Waive Fine',
      '继续处理下一条': 'Continue with the Next Item',
      '会员列表': 'Member List',
      '选中会员': 'Selected Member',
      '冻结原因': 'Freeze Reason',
      '续期天数': 'Renewal Days',
      '通过审核': 'Approve',
      '冻结': 'Freeze',
      '解冻': 'Unfreeze',
      '续期': 'Renew',
      '账号列表': 'Account List',
      '角色调整': 'Role Update',
      '角色': 'Role',
      '保存角色': 'Save Role',
      '提醒策略配置': 'Reminder Policy Configuration',
      '当前策略': 'Current Policy',
      '编辑策略': 'Edit Policy',
      '到期前提醒天数': 'Days Before Due Reminder',
      '逾期后提醒天数': 'Days After Overdue Reminder',
      '保存策略': 'Save Policy',
      '公告列表': 'Notice List',
      '编辑公告': 'Edit Notice',
      '新建公告': 'New Notice',
      '标题': 'Title',
      '内容': 'Content',
      '是否立即生效': 'Show Immediately',
      '立即显示': 'Show Now',
      '先保存不显示': 'Save Without Showing',
      '保存公告': 'Save Notice',
      '切换到新建': 'Switch to New',
      '通知中心': 'Notification Center',
      '通知列表': 'Notification List',
      '我的借阅': 'My Loans',
      '我的预约': 'My Reservations',
      '通知中心': 'Notification Center',
      '返回馆藏检索': 'Back to Catalog',
      '查看推荐': 'View Recommendations',
      '我的预约': 'My Reservations',
      '图书详情': 'Book Details',
      '查看详情': 'View Details',
      '下一步': 'Next Step',
      '搜索': 'Search',
      '立即搜索': 'Search Now',
      '立即筛选': 'Filter Now',
      '按编号看详情': 'Open Details by ID',
      '继续找书': 'Keep Browsing',
      '查看同类图书': 'View Similar Books',
      '同类图书': 'Similar Books',
      '系统自动分配': 'Assign Automatically',
      '加入预约': 'Join Reservation Queue',
      '当前操作': 'Current Action',
      '通知': 'Notification',
      '未读': 'Unread',
      '已读': 'Read',
      '系统通知': 'System Notice',
      '提示': 'Hint',
      '原因': 'Reason',
      '金额': 'Amount',
      '可以借阅': 'Available to Borrow',
      '支付时间': 'Processed Time',
      '处理人': 'Handled By',
      '币种': 'Currency',
      '是': 'Yes',
      '否': 'No',
      '未知': 'Unknown',
      '未知作者': 'Unknown Author',
      '未知状态': 'Unknown Status',
      '暂无': 'N/A',
      '未填写': 'Not Provided',
      '暂无邮箱': 'No Email',
      '暂无位置': 'No Location',
      '暂无内容': 'No Content',
      '暂无简介': 'No Description',
      '暂无原因说明': 'No Reason Provided',
      '搜索与推荐': 'Search and Recommendations',
      '从这里直接搜馆藏；如果暂时没有目标，就让系统先给你推荐几本。': 'Search the catalog directly here. If you do not have a target yet, let the system recommend a few books first.',
      '打开完整书目页': 'Open Full Book List',
      '关键词': 'Keyword',
      '输入书名、作者或分类关键词': 'Enter a title, author, or category keyword',
      '查询馆藏': 'Search Catalog',
      '我的借阅': 'My Loans',
      '查看到期时间，直接续借符合规则的图书': 'Check due times and renew eligible books directly.',
      '我的预约': 'My Reservations',
      '看排队位置、READY 倒计时和取消入口': 'Check queue position, pickup countdowns, and cancel actions.',
      '通知中心': 'Notification Center',
      '优先处理到期提醒、逾期提醒和可取书提醒': 'Prioritize due reminders, overdue reminders, and pickup reminders.',
      '账号状态': 'Account Status',
      '正在准备你的借阅信息': 'Preparing your loan information',
      '页面会自动加载当前借阅记录，并把可续借的图书直接放出按钮。': 'The page loads your current loans automatically and shows direct renewal buttons for eligible items.',
      '借阅列表会显示在这里': 'The loan list will appear here',
      '如果当前没有借书，我会直接告诉你下一步去哪里找书。': 'If you have no current loans, the page will tell you where to look for books next.',
      '续借结果会显示在这里': 'The renewal result will appear here',
      '如果你要还书，请把书带到服务台，由馆员在“借书 / 还书”页面办理。': 'If you need to return a book, bring it to the desk and let a librarian handle it on the Checkout / Check-in page.',
      '当前还有': 'Still Active',
      '本书未归还': 'books not yet returned',
      '当前没有未归还图书': 'There are no unreturned books right now',
      '可以在借阅列表里直接续借符合规则的图书；如果要还书，请把书带到服务台。': 'You can renew eligible books directly from the loan list. For returns, bring the book to the desk.',
      '如果想借书，可以直接去图书列表浏览馆藏。': 'If you want to borrow a book, open the catalog directly.',
      '去图书列表': 'Go to Book List',
      '你当前还没有借阅记录': 'You do not have any loan records yet',
      '可以先去图书列表看看感兴趣的书，找到后直接借阅。': 'Browse the catalog first, then borrow a book directly once you find one.',
      '已逾期': 'Overdue',
      '借出时间': 'Borrowed At',
      '应还时间': 'Due Time',
      '尚未归还': 'Not Returned Yet',
      '续借这本书': 'Renew This Book',
      '借阅列表': 'Loan List',
      '我的预约': 'My Reservations',
      '预约列表会显示在这里': 'The reservation list will appear here',
      '如果有书暂时借不到，可以在图书详情页或这里直接提交预约。': 'If a book is not available right now, submit a reservation here or from the detail page.',
      '看排队位置、READY 倒计时和取消入口': 'Check queue position, pickup countdowns, and cancel actions.',
      '查看全部': 'Show All',
      '只看未读': 'Unread Only',
      '只看已读': 'Read Only',
      '通知列表会显示在这里': 'Notifications will appear here',
      '标记已读后的结果会显示在这里': 'The result of marking as read will appear here',
      '查看推荐': 'View Recommendations',
      '推荐你看看这': 'Recommended',
      '输入书名、作者、分类或图书编号后，列表会自动更新；也可以结合作者、分类和可借状态一起筛选。': 'Enter a title, author, category, or Book ID. The list updates automatically, and you can combine filters as needed.',
      '全部分类': 'All Categories',
      '文学': 'Literature',
      '科幻': 'Science Fiction',
      '奇幻': 'Fantasy',
      '推理': 'Mystery',
      '历史': 'History',
      '传记': 'Biography',
      '哲学': 'Philosophy',
      '心理': 'Psychology',
      '商业': 'Business',
      '科学': 'Science',
      '计算机': 'Computing',
      '可借状态': 'Availability',
      '只看现在可借': 'Available Now Only',
      '先挑书；想继续借阅、预约或查看借阅记录时，再登录进入对应功能页面。': 'Pick a book first. Sign in only when you want to borrow, reserve, or view your loan records.',
      '查看我的账号': 'View My Account',
      '图书详情': 'Book Details',
      '这本书当前的馆藏情况': 'Current Status of This Book',
      '当前可借': 'Available Now',
      '维修中': 'Under Maintenance',
      '如果这本书当前有多个可借副本，你可以先选一个，再决定怎么借。': 'If several copies are available, choose one first and then decide how to borrow it.',
      '这里会显示可借副本': 'Available copies will appear here',
      '如果这本书暂时不想借，或者你想继续比较，也可以直接看同类书。': 'If you do not want to borrow it now or want to compare more options, open similar books directly.',
      '如果这个分类下没有更多书，可以回到列表页换一个关键词。': 'If there are no more books in this category, go back to the list and try another keyword.',
      '接下来做什么': 'What Next',
      '预约排队': 'Reservation Queue',
      '先给你看一批更容易上手的热门馆藏。': 'Start with a small set of popular books that are easier to pick from.',
      '暂时借不到': 'Not Available Right Now',
      '可借数量': 'Available Copies',
      '查看同类图书': 'View Similar Books',
      '点击“查看同类图书”后，这里会出现结果': 'Results will appear here after you click "View Similar Books"',
      '适合当前这本书暂时借不到时继续找同主题替代项。': 'Useful when the current book is unavailable and you want alternatives.',
      '借阅所选副本': 'Borrow Selected Copy',
      '操作结果会显示在这里': 'The result will appear here',
      '借阅成功、预约成功，或者失败原因，都会直接告诉你。': 'Borrowing results, reservation results, and failure reasons are shown directly here.',
      '你可以直接让系统自动分配副本，也可以先选一个具体副本再借阅；如果当前没有可借副本，再加入预约。': 'You can let the system assign a copy automatically, or select a specific copy first. If no copy is available, join the reservation queue.',
      '你可以手动指定一个副本借阅；如果不想选，直接点“系统自动分配”。': 'You can choose a specific copy to borrow, or use "Assign Automatically" if you do not want to choose.',
      '当前没有可借副本': 'No Copies Available Now',
      '这本书现在没有可直接借出的副本。如果你还想看，直接加入预约即可。': 'No copy can be borrowed right now. Join the reservation queue if you still want it.',
      '先看今天要处理什么，再直接进入对应任务页。': 'See what needs attention today and jump straight to the right task page.',
      '现在最常做什么': 'Most Common Tasks',
      '如果读者来柜台还书，直接进入“借书 / 还书”，从借阅中列表点一条记录就能带入借阅编号。': 'When a reader returns a book at the desk, open Checkout / Check-in and pick the loan from the active list.',
      '当前账号可直接处理后台业务': 'This account can directly use the admin portal',
      '你也可以切到读者服务页，从普通用户视角检查前台体验。': 'You can also switch to Reader Services to inspect the public-facing experience.',
      '当前账号可直接处理借还书和馆藏业务': 'This account can directly handle circulation and catalog work',
      '当前账号可直接进入读者服务': 'This account can directly open Reader Services',
      '你已登录管理员账号，可以直接进入管理后台，也可以进入读者服务查看普通用户侧的实际体验。': 'You are signed in as an administrator. Open the admin portal directly, or switch to Reader Services to inspect the reader-facing experience.',
      '你已登录馆员账号，可以直接进入管理后台处理借还、馆藏和罚款业务。': 'You are signed in as a librarian. Open the admin portal directly to handle circulation, catalog, and fines.',
      '你已登录读者账号，选好书后可以直接进入读者服务办理借阅、预约和查看通知。': 'You are signed in as a reader. After choosing a book, open Reader Services directly to borrow, reserve, or review notifications.',
      '图书总数': 'Books',
      '账号总数': 'Accounts',
      '借阅中': 'Active Loans',
      '待审核会员': 'Pending Members',
      '借书办理': 'Checkout',
      '优先输入读者编号和图书编号，系统会自动分配可借副本；如果手里已经拿到实体书，也可以直接录入条码。': 'Enter a reader ID and Book ID first. The system can assign an available copy automatically, or you can scan a barcode if the physical book is already at hand.',
      '办理借书': 'Process Checkout',
      '还书办理': 'Check-in',
      '先从借阅中列表点选一条记录，系统会自动带入借阅编号；也可以手动输入借阅编号再还书。': 'Pick an active loan from the list below to fill the Loan ID automatically, or type the Loan ID manually before processing the return.',
      '归还结果': 'Return Condition',
      '正常归还': 'Returned in Good Condition',
      '书籍破损': 'Damaged Book',
      '书籍遗失': 'Lost Book',
      '办理还书': 'Process Return',
      '借阅中列表': 'Active Loan List',
      '这里会列出当前所有未归还图书。点一条记录即可自动带入借阅编号去办理还书。': 'This list shows every book that has not yet been returned. Select one to fill the Loan ID automatically.',
      '按读者、图书名、条码或编号搜索': 'Search by reader, book title, barcode, or ID',
      '刷新借阅中列表': 'Refresh Active Loans',
      '当前没有借阅中的图书': 'There are no active loans right now',
      '只要有未归还图书，这里就会自动显示对应借阅记录。': 'As soon as there are unreturned books, the related loan records appear here automatically.',
      '当前概览': 'Current Summary',
      '借书办理成功': 'Checkout Successful',
      '继续办理下一位': 'Continue with the Next Reader',
      '还书办理成功': 'Return Processed',
      '遗失登记成功': 'Lost Book Recorded',
      '破损登记成功': 'Damaged Book Recorded',
      '副本状态': 'Copy Status',
      '归还时间': 'Returned At',
      '罚款金额': 'Fine Amount',
      '罚款原因': 'Fine Reason',
      '罚款状态': 'Fine Status',
      '去处理这笔罚款': 'Handle This Fine',
      '查看罚款列表': 'View Fine List',
      '请先选择要归还的借阅记录': 'Select a loan record to return first',
      '可以直接从下方借阅中列表点一条记录，系统会自动带入借阅编号。': 'Pick a record from the active loan list below and the Loan ID will be filled automatically.',
      '已选中借阅编号': 'Selected Loan ID',
      '现在可以直接点击“办理还书”，也可以先修改归还结果再提交。': 'You can process the return now, or change the return condition before submitting.',
      '带入还书': 'Fill for Return',
      '罚款记录会显示在这里': 'Fine records will appear here',
      '默认展示当前筛选条件下的罚款记录，你也可以切换到未缴、已缴或已减免。': 'Fine records for the current filter are shown by default. You can switch to unpaid, paid, or waived.',
      '罚款处理结果会显示在这里': 'The fine-handling result will appear here',
      '处理成功后，列表会自动刷新，方便继续处理下一条。': 'After a successful update, the list refreshes automatically so you can continue.',
      '当前筛选条件下没有罚款记录': 'No fines match the current filter',
      '未缴罚款会直接显示“标记已缴”和“减免”按钮。': 'Unpaid fines show direct actions for payment or waiver.',
      '会员列表会显示在这里': 'The member list will appear here',
      '默认优先展示待审核会员；点一位会员后，右侧就能直接处理。': 'Pending members are shown first. Select one to handle it on the right.',
      '先在左侧选中一位会员': 'Select a member on the left first',
      '选中后才能执行审核、冻结、解冻和续期。': 'You can approve, freeze, unfreeze, or renew only after selecting a member.',
      '审核和状态变更结果会显示在这里': 'Results of reviews and status changes will appear here',
      '当前筛选条件下没有会员': 'No members match the current filter',
      '可以切换状态过滤器，或者稍后再回来查看。': 'Change the status filter or come back later.',
      '会员已通过审核': 'Member Approved',
      '会员已冻结': 'Member Frozen',
      '会员已解冻': 'Member Unfrozen',
      '会员已续期': 'Membership Renewed',
      '没有找到账号': 'No accounts found',
      '可以换个关键词再试。': 'Try another keyword.',
      '馆藏副本只显示这本书的馆藏副本。': 'Only copies of this book are shown here.',
      '馆藏副本状态已更新': 'Copy Status Updated',
      '馆藏副本已更新': 'Copy Updated',
      '馆藏副本已创建': 'Copy Created',
      '馆藏副本页只处理条码、位置和副本状态。': 'This page manages the barcode, location, and status of a library copy.',
      '副本列表会显示在这里': 'The copy list will appear here',
      '点选副本卡片后，右侧可以直接编辑条码、位置和状态。': 'Select a copy card to edit its barcode, location, and status on the right.',
      '先选中副本，或切换到新建模式': 'Select a copy first, or switch to new mode',
      '状态变更和副本编辑成功后，列表会自动刷新。': 'After saving or changing status, the list refreshes automatically.',
      '当前没有符合条件的副本': 'No copies match the current filter',
      '可以调整筛选条件，或者直接新建副本。': 'Adjust the filter or create a new copy.',
      '可以切换状态筛选，或者稍后再回来查看。': 'Switch the status filter or come back later.',
      '新建馆藏副本': 'New Library Copy',
      '编辑馆藏副本': 'Edit Library Copy',
      '填写图书编号、条码、位置和状态后即可创建。': 'Fill in the Book ID, barcode, location, and status to create the copy.',
      '修改后保存，或只更新状态。': 'Save the changes, or update only the status.',
      '保存修改': 'Save Changes',
      '只更新状态': 'Update Status Only',
      '图书列表会显示在这里': 'The book list will appear here',
      '先找到图书，再决定是编辑图书信息，还是进入副本页继续管理馆藏副本。': 'Find a book first, then decide whether to edit the book record or continue to its library copies.',
      '点选图书后，右侧可以直接编辑；如果要管理馆藏副本，直接点“查看馆藏副本”即可。': 'Select a book to edit it on the right, or open its library copies directly.',
      '点图书卡片可以编辑；点“查看馆藏副本”可以继续管理这本书的实体副本。': 'Select a book card to edit it, or open its library copies to manage physical holdings.',
      '先选中一本书，或新建图书': 'Select a book first, or create a new one',
      '右侧只负责编辑图书信息；馆藏副本请从图书卡片进入对应页面处理。': 'The right panel edits the book record. Manage copies from the book card entry.',
      '保存成功后，左侧列表会自动刷新到最新状态。': 'After saving, the list on the left refreshes automatically.',
      '当前没有符合条件的图书': 'No books match the current filter',
      '可以修改搜索条件，或者直接新建图书。': 'Adjust the search or create a new book.',
      '新增、编辑图书；副本仍从图书页继续管理。': 'Create or edit books here. Library copies are still managed from the book page.',
      '图书已更新': 'Book Updated',
      '图书已创建': 'Book Created',
      '新建图书': 'New Book',
      '图书信息已保存，左侧列表会自动同步最新状态。': 'Book information has been saved and the list updates automatically.',
      '查看馆藏副本': 'View Library Copies',
      '这里看全馆概况、热门借阅和当前逾期情况。': 'View the overall status, popular loans, and current overdue items here.',
      '总体概况': 'Overview',
      '热门借阅': 'Popular Loans',
      '当前逾期': 'Current Overdue',
      '还没有热门借阅数据': 'No popular-loan data yet',
      '只要产生借阅记录，这里就会自动汇总。': 'As soon as loans exist, this section will summarize them automatically.',
      '当前没有逾期借阅': 'There are no overdue loans now',
      '只要出现逾期记录，这里就会列出来。': 'Any overdue loans will be listed here automatically.',
      '这里可以发布新的公告，或修改当前正在首页显示的公告。': 'Publish a new notice here, or update the one currently shown on the home page.',
      '还没有公告': 'No notices yet',
      '先创建一条公告。': 'Create a notice first.',
      '保存为“启用”后，首页公告会立即切换为这条内容。': 'Once saved as enabled, the home-page notice switches to this content immediately.',
      '在这里查看当前提醒规则，并按需要调整提醒天数。': 'View the current reminder rules here and adjust the reminder days as needed.',
      '用半角逗号分隔天数，例如 `3,1,0` 表示到期前 3 天、1 天和当天提醒。': 'Use commas to separate days. For example, `3,1,0` means reminders 3 days before, 1 day before, and on the due day.',
      '正在加载当前提醒策略': 'Loading the current reminder policy',
      '这里会展示到期提醒、逾期提醒和当前启用角色。': 'This section shows due reminders, overdue reminders, and enabled roles.',
      '保存策略后的结果会显示在这里': 'The save result for the policy will appear here',
      '保存成功后，这里会显示最新生效结果。': 'After saving, the latest effective result will appear here.',
      '当前默认策略': 'Current Default Policy',
      '下面展示的是当前生效中的提醒规则。': 'The currently effective reminder rules are shown below.',
      '提醒策略已更新': 'Reminder Policy Updated',
      '按时间、操作者、操作类型和对象类型筛选后台记录。': 'Filter back-office records by time, operator, action type, and object type.',
      '查询结果会显示在这里': 'Search results will appear here',
      '日志会按时间顺序展示，适合追踪后台关键操作和数据变更。': 'Logs are shown in chronological order to help track key back-office actions and data changes.',
      '当前条件下没有日志记录': 'No logs match the current filter',
      '可以放宽筛选条件，或者调整时间范围后再试。': 'Broaden the filters or adjust the time range and try again.',
      '每条记录都包含操作者、操作类型、对象和变更内容。': 'Each record includes the operator, action type, object, and changed content.',
      '先看看这些推荐书': 'Start with These Recommendations',
      '默认先展示一批推荐馆藏。输入关键词或筛选条件后，结果会自动切换。': 'A short set of recommended books is shown first. Results switch automatically when you search or change filters.',
      '如果你是从馆藏列表点进来的，系统会自动带上图书编号并直接展示详情。': 'If you came from the catalog, the Book ID is filled in automatically.',
      '先输入图书编号查看详情': 'Enter a Book ID to view details',
      '请确认图书编号是否正确，或者回到馆藏列表重新查找。': 'Check whether the Book ID is correct, or return to the catalog and search again.',
      '先确认这本书是否还可借，再决定要不要登录进入读者服务继续办理借阅或预约。': 'Check whether the book is available first, then decide whether to sign in and borrow or reserve it.',
      '馆藏情况': 'Catalog Status',
      '建议预约': 'Reservation Recommended',
      '没有找到这本书': 'Book Not Found',
      '回到馆藏检索': 'Back to Catalog',
      '已上架': 'Active',
      '系统默认': 'System Default',
      '读者首页只围绕三件事展开：我的账号状态、我要找什么书、我接下来要去处理哪类记录。': 'The reader home focuses on three things: your account status, what to read next, and what to handle next.',
      '账号状态': 'Account Status',
      '账号状态正常，可以继续借阅、续借和预约。': 'The account is active and can keep borrowing, renewing, and reserving books.',
      '查看我的借阅': 'View My Loans',
      '查看通知中心': 'View Notification Center',
      '会员状态': 'Membership Status',
      '有效期至': 'Valid Until',
      '个性化推荐': 'Personalized Recommendations',
      '搜索与推荐': 'Search and Recommendations',
      '从这里直接搜馆藏；如果暂时没有目标，就让系统先给你推荐几本。': 'Search the catalog directly here. If you do not have a target yet, let the system recommend a few books.',
      '打开完整书目页': 'Open Full Book List',
      '关键词': 'Keyword',
      '输入书名、作者或分类关键词': 'Enter a title, author, or category keyword',
      '查询馆藏': 'Search Catalog',
      '先搜一本书，或者直接看推荐': 'Search for a book first, or open recommendations',
      '输入书名、作者、分类关键词来查馆藏；如果暂时没有目标，就点右上角的“查看推荐”。': 'Search the catalog by title, author, or category. If you are not sure what to read, open recommendations.',
      '查看推荐': 'View Recommendations',
      '默认先给你看一小批推荐书目。输入关键词、作者或分类后，下面会自动切换结果。': 'A short set of recommended books is shown first. Search by keyword, author, or category and the results below switch automatically.',
      '快速预约': 'Quick Reservation',
      '输入图书 ID 后，我会帮你提交预约。': 'Enter a Book ID and the system will submit the reservation for you.',
      '提交预约': 'Submit Reservation',
      '推荐结果会结合你的借阅记录、热门馆藏和新到馆图书动态生成。': 'Recommendations are generated from your loan history, popular books, and new arrivals.',
      '暂时还没有推荐结果': 'No recommendations yet',
      '可以先完成一次借阅，系统会根据借阅记录生成更贴近的推荐。': 'Complete a loan first, then recommendations will become more relevant.',
      '先去浏览馆藏': 'Browse Catalog First',
      '这里集中展示你的借阅记录、到期时间和续借入口；如果要还书，请把书带到服务台办理。': 'Your loan records, due times, and renewal actions are shown here. Returns still need to be handled at the desk.',
      '刷新借阅': 'Refresh Loans',
      '借阅概览': 'Loan Overview',
      '当前未还': 'Active Loans',
      '这里集中展示预约队列、READY 取书倒计时和取消入口，不再需要你手动输入预约编号才能操作。': 'Reservation queues, pickup countdowns, and cancel actions are shown here so you do not need to type a Reservation ID by hand.',
      '刷新预约': 'Refresh Reservations',
      '预约列表': 'Reservation List',
      '去图书列表找书': 'Go to Book List',
      '如果你已经在图书详情页，就直接在那里点“加入预约”会更顺手。': 'If you are already on the book detail page, it is easier to join the reservation queue there.',
      '你当前还没有预约记录': 'You do not have any reservation records yet',
      '预约结果会显示在这里': 'The reservation result will appear here',
      '无论是提交预约还是取消预约，我都会告诉你目前排到哪里，或者什么时候去取书。': 'After creating or cancelling a reservation, the page tells you your queue position or pickup time.',
      '这里集中展示到期提醒、取书提醒和系统消息，并支持直接标记已读。': 'Due reminders, pickup reminders, and system messages are shown here, and you can mark them as read directly.',
      '刷新通知': 'Refresh Notifications',
      '通知筛选': 'Notification Filter',
      '未读消息会保留醒目状态，方便你优先处理到期和取书提醒。': 'Unread messages stay highlighted so you can handle due and pickup reminders first.',
      '操作反馈': 'Action Feedback',
      '已读后会同步刷新列表，让你更容易聚焦剩余未处理消息。': 'After marking an item as read, the list refreshes so you can focus on what is still pending.',
      '还没有通知': 'No notifications yet',
      '当前还没有通知': 'There are no notifications right now',
      '当图书到期、逾期或预约可取时，提醒会第一时间出现在这里。': 'When a book is due, overdue, or ready for pickup, the reminder appears here immediately.',
      '通知已标记为已读': 'Notification Marked as Read',
      '这个邮箱已经注册过了，可以直接去登录。': 'This email is already registered. Go to sign in directly.',
      '这些内容还没填对': 'Some fields still need correction',
      '把下面这些内容改对后，再提交一次。': 'Fix the following items and submit again.',
      '注册失败，请先修改标出的内容。': 'Registration failed. Fix the highlighted items first.',
      '注册失败，请按提示修改后再试。': 'Registration failed. Follow the guidance and try again.',
      '邮箱格式不正确，请输入带 @ 的完整邮箱地址。': 'The email format is invalid. Enter a complete email address with @.',
      '邮箱格式不正确，请输入类似 reader@example.com 的地址。': 'The email format is invalid. Enter an address like reader@example.com.',
      '密码至少需要 6 位。': 'The password must be at least 6 characters long.',
      '姓名不能为空。': 'Name cannot be empty.',
      '注册没有提交成功': 'Registration Was Not Submitted',
      '账号已经提交，管理员审核通过后就可以登录并进入读者服务。': 'The account has been submitted. Once approved by an administrator, it can sign in and use Reader Services.',
      '操作未完成': 'Operation Incomplete',
      '请稍后重试。': 'Please try again shortly.',
      '请求编号：{requestId}': 'Request ID: {requestId}',
      '查看罚款记录': 'View Fine Records',
      '查看会员审核': 'View Member Review',
      '柜台借书、还书都从这里处理。': 'Handle all desk checkout and check-in tasks here.',
      '进入页面': 'Open Page',
      '查看未缴罚款，登记已缴或减免。': 'Review unpaid fines and mark them paid or waived.',
      '审核、冻结、解冻和续期。': 'Approve, freeze, unfreeze, and renew memberships.',
      '查看账号角色并调整管理员、馆员、读者身份。': 'Review account roles and switch between administrator, librarian, and reader.',
      '查看热门借阅、逾期和罚款概况。': 'View popular loans, overdue items, and fine summaries.',
      '发布或调整当前首页公告。': 'Publish or update the notice currently shown on the home page.',
      '查看后台操作记录。': 'Review back-office operation records.',
      '配置到期与逾期提醒规则。': 'Configure due and overdue reminder rules.',
      '先筛出未处理的罚款，再直接标记已缴或减免。': 'Filter pending fines first, then mark them paid or waived.',
      '刷新罚款': 'Refresh Fines',
      '罚款记录': 'Fine Records',
      '书籍损坏赔偿': 'Damaged Book Compensation',
      '用户 ID': 'User ID',
      '先筛出要处理的会员，再选中一位，右侧直接完成审核、冻结、解冻或续期。': 'Filter the members you need to handle, then select one to approve, freeze, unfreeze, or renew.',
      '待审核优先': 'Pending First',
      '先选中一位会员': 'Select a member first',
      '如果列表为空，也就没有可处理的会员。': 'If the list is empty, there are no members to handle right now.',
      '成功后列表会自动刷新，方便继续处理下一位。': 'After success, the list refreshes automatically so you can continue with the next person.',
      '刷新账号': 'Refresh Accounts',
      '逾期中': 'Overdue',
      '未缴罚款': 'Unpaid Fines',
      '借阅次数': 'Borrow Count',
      '刷新公告': 'Refresh Notices',
      '当前显示中': 'Visible on Home',
      '未显示': 'Hidden',
      '重新加载': 'Reload',
      '到期前提醒': 'Before Due',
      '逾期后提醒': 'After Overdue',
      '启用角色': 'Enabled Roles',
      '新建副本': 'New Copy',
      '编辑副本': 'Edit Copy',
      '当前位置：': 'Current location:',
      '上架': 'Active',
      '下架': 'Inactive',
      '上架状态': 'Availability',
      '破损赔偿金额': 'Damaged Compensation Amount',
      '遗失赔偿金额': 'Lost Compensation Amount',
      '保存后列表会自动同步；馆藏副本请从左侧卡片进入。': 'After saving, the list updates automatically. Open library copies from the card on the left.',
      '图书总数': 'Books',
      '当前找到 2 个副本': 'Found 2 copies',
      '开始找书': 'Start Searching',
      '从这里直接进入你现在最需要的入口，不用先猜应该点哪里。': 'Jump straight to the task you need now without guessing where to click.',
      '按书名、作者、分类和可借状态快速筛选': 'Filter quickly by title, author, category, and availability.',
      '继续借、看预约、看通知都从这里进入': 'Open renewals, reservations, and notifications here.',
      '审批会员、借还书、罚款、公告都在这里': 'Handle approvals, circulation, fines, and notices here.',
      '先看一批当前更适合直接下手的馆藏，想继续再进入完整检索页。': 'Start with a short list of books worth checking now, then open the full catalog if needed.',
      '这里是首页精选展示，不是全部结果。想继续找，直接进入完整馆藏检索。': 'This is a curated home-page section, not the full result list. Open the full catalog to continue browsing.',
      '先找书也可以；如果要借阅、预约或处理后台业务，再进入对应入口。': 'You can browse first. Sign in only when you need to borrow, reserve, or handle back-office work.',
      '搜索框和筛选条件会实时联动，下面只展示一小批更值得你先看的书。': 'The search box and filters update together in real time. Only a short list worth checking first is shown below.',
      '只看现在能借': 'Available Now Only',
      '先展示一批更容易借到、也更值得先看的馆藏。': 'Start with a short list of books that are easier to borrow and worth checking first.',
      '先放入预约': 'Reserve First',
      '接下来': 'Next',
      '看到想借的书后，直接点“查看详情”，再决定是立即借阅还是加入预约。': 'After spotting a book you want, open its details and then decide whether to borrow it now or join the reservation queue.',
      '看我的预约': 'View My Reservations',
      '如果你是从图书页点进来的，系统会自动带入该图书的编号，只显示这本书的馆藏副本。': 'If you entered from the book page, the Book ID is filled in automatically and only the copies for this book are shown.',
      '点选任意副本卡片，即可在右侧修改位置、条码和状态。': 'Select any copy card to edit its location, barcode, and status on the right.',
      '柜台借书、还书都在这里办理。还书时，直接从下方“借阅中列表”点一条记录即可。': 'Handle all desk checkout and check-in tasks here. For returns, just pick a record from the active loan list below.',
      '点击任意一条记录，会自动带入借阅编号到上方“还书办理”表单。': 'Click any record to fill its Loan ID into the return form above automatically.',
      '副本编号': 'Copy ID',
      '查看罚款': 'View Fines',
      '办理结果': 'Result',
      '办理结果会显示在这里': 'The result will appear here',
      '借书或还书成功后，这里会明确告诉你发生了什么，以及下一步该去哪处理。': 'After checkout or check-in, this section tells you what happened and where to go next.',
      '你可以处理会员审核、图书、借还、罚款、日志和提醒策略。': 'You can handle member review, books, circulation, fines, logs, and reminder rules.',
      '编辑图书': 'Edit Book',
      '刷新报表': 'Refresh Report',
      '全部操作': 'All Actions',
    },
  };

  const phraseReplacements = [
    { pattern: /^当前可借馆藏共 (\d+) 本，这里先展示 (\d+) 本$/, translate: (_, total, shown) => `There are ${total} available books in the catalog. Showing ${shown} here.` },
    { pattern: /^馆藏共 (\d+) 本，这里先展示 (\d+) 本$/, translate: (_, total, shown) => `There are ${total} books in the catalog. Showing ${shown} here.` },
    { pattern: /^当前共有 (\d+) 条借阅中记录$/, translate: (_, count) => `There are ${count} active loan records` },
    { pattern: /^当前共有 (\d+) 条罚款记录$/, translate: (_, count) => `There are ${count} fine records` },
    { pattern: /^当前共有 (\d+) 位会员$/, translate: (_, count) => `There are ${count} members` },
    { pattern: /^当前找到 (\d+) 本图书$/, translate: (_, count) => `Found ${count} books` },
    { pattern: /^当前找到 (\d+) 个馆藏副本$/, translate: (_, count) => `Found ${count} library copies` },
    { pattern: /^当前可选 (\d+) 个副本$/, translate: (_, count) => `${count} copies are available to choose from` },
    { pattern: /^查询到 (\d+) 条日志$/, translate: (_, count) => `Found ${count} log records` },
    { pattern: /^为你挑了 (\d+) 本推荐书$/, translate: (_, count) => `Showing ${count} recommended books` },
    { pattern: /^先给你看 (\d+) 本推荐书$/, translate: (_, count) => `Here are ${count} recommended books to start with` },
    { pattern: /^推荐你看看这 (\d+) 本书$/, translate: (_, count) => `Recommended: ${count} books for you` },
    { pattern: /^借阅编号 (.+) 已创建，到期时间为 (.+)。$/, translate: (_, loanId, dueAt) => `Loan ID ${loanId} has been created. Due by ${dueAt}.` },
    { pattern: /^借阅编号 (.+) 已处理，本次未生成罚款，副本状态已更新为“(.+)”。$/, translate: (_, loanId, status) => `Loan ID ${loanId} has been processed. No fine was generated. Copy status is now "${translateText(status, 'en')}".` },
    { pattern: /^借阅编号 (.+) 已处理，系统已生成罚款 (.+)，原因：(.+)。$/, translate: (_, loanId, amount, reason) => `Loan ID ${loanId} has been processed. A fine of ${amount} was generated. Reason: ${translateText(reason, 'en')}.` },
    { pattern: /^罚款 #(.+) 的状态已经更新为 (.+)。$/, translate: (_, fineId, status) => `Fine #${fineId} has been updated to ${translateText(status, 'en')}.` },
    { pattern: /^罚款 #(.+)$/, translate: (_, fineId) => `Fine #${fineId}` },
    { pattern: /^馆藏副本 #(.+)$/, translate: (_, copyId) => `Copy #${copyId}` },
    { pattern: /^副本 #(.+)$/, translate: (_, copyId) => `Copy #${copyId}` },
    { pattern: /^编辑公告（编号 (.+)）$/, translate: (_, id) => `Edit Notice (ID ${id})` },
    { pattern: /^编辑图书（编号 (.+)）$/, translate: (_, id) => `Edit Book (ID ${id})` },
    { pattern: /^编辑馆藏副本（编号 (.+)）$/, translate: (_, id) => `Edit Copy (ID ${id})` },
    { pattern: /^图书编号 (.+)$/, translate: (_, id) => `Book ID ${id}` },
    { pattern: /^读者编号 (.+)$/, translate: (_, id) => `Reader ID ${id}` },
    { pattern: /^账号编号 (.+)$/, translate: (_, id) => `Account ID ${id}` },
    { pattern: /^操作者编号 (.+)$/, translate: (_, id) => `Operator ID ${id}` },
    { pattern: /^借阅编号 (.+)$/, translate: (_, id) => `Loan ID ${id}` },
    { pattern: /^预约编号 (.+)$/, translate: (_, id) => `Reservation ID ${id}` },
    { pattern: /^馆藏副本编号 (.+)$/, translate: (_, id) => `Copy ID ${id}` },
    { pattern: /^图书编号 (.+) \/ 条码 (.+)$/, translate: (_, id, barcode) => `Book ID ${id} / Barcode ${barcode}` },
    { pattern: /^Book ID (.+) \/ 条码 (.+)$/, translate: (_, id, barcode) => `Book ID ${id} / Barcode ${barcode}` },
    { pattern: /^当前位置：(.*)$/, translate: (_, location) => `Current location: ${location}` },
    { pattern: /^位置 (.+)$/, translate: (_, location) => `Location ${location}` },
    { pattern: /^条码 (.+)$/, translate: (_, barcode) => `Barcode ${barcode}` },
    { pattern: /^条码：(.*)，应还时间：(.*)$/, translate: (_, barcode, dueAt) => `Barcode: ${barcode}, Due Time: ${dueAt}` },
    { pattern: /^读者 (.+)$/, translate: (_, value) => `Reader ${value}` },
    { pattern: /^图书 (.+)$/, translate: (_, value) => `Book ${value}` },
    { pattern: /^可借 (\d+) 本$/, translate: (_, count) => `${count} copies available` },
    { pattern: /^(\d+) 小时 (\d+) 分钟$/, translate: (_, hours, minutes) => `${hours}h ${minutes}m` },
    { pattern: /^(\d+) 次$/, translate: (_, count) => `${count} times` },
    { pattern: /^当前会员状态：(.+)。$/, translate: (_, status) => `Current membership status: ${translateText(status, 'en')}.` },
    { pattern: /^“(.+)”分类下有 (\d+) 本相关图书$/, translate: (_, category, count) => `${count} related books were found in the "${category}" category` },
    { pattern: /^“(.+)”已经从未读状态中移除。$/, translate: (_, title) => `"${title}" was marked as read.` },
    { pattern: /^“(.+)”下没有结果，可以换个关键词试试。$/, translate: (_, keyword) => `No results were found for "${keyword}". Try another keyword.` },
    { pattern: /^处理 (\d+) 个待审核会员$/, translate: (_, count) => `Review ${count} pending members` },
    { pattern: /^查看 (\d+) 条借阅中记录$/, translate: (_, count) => `View ${count} active loans` },
    { pattern: /^可借 (.+) 本$/, translate: (_, count) => `${count} copies available` },
    { pattern: /^图书已经为你保留，请在 (.+) 前完成借阅。$/, translate: (_, deadline) => `The book has been reserved for you. Complete checkout before ${deadline}.` },
    { pattern: /^你已经进入预约队列，目前排队序号为 (.+)。$/, translate: (_, queueNo) => `Your reservation is in the queue. Current position: ${queueNo}.` },
    { pattern: /^这本书已经续借成功，新的到期时间是 (.+)。$/, translate: (_, dueAt) => `This book was renewed successfully. New due time: ${dueAt}.` },
    { pattern: /^到期提醒已更新为 (.+)；逾期提醒已更新为 (.+)。$/, translate: (_, dueDays, overdueDays) => `Due reminders are now set to ${dueDays}; overdue reminders are now set to ${overdueDays}.` },
    { pattern: /^图书 #(.+) 的预约已经从你的待处理列表中移除。$/, translate: (_, id) => `The reservation for Book ID ${id} has been removed from your pending list.` },
  ];

  const statusLabels = {
    'zh-CN': {
      ACTIVE: '进行中', AVAILABLE: '可借', ON_LOAN: '外借中', MAINTENANCE: '维修中', LOST: '已丢失',
      REMOVED: '已下架', RETURNED: '已归还', QUEUED: '排队中', READY_FOR_PICKUP: '可取书',
      COMPLETED: '已完成', CANCELLED: '已取消', PENDING: '待处理', FROZEN: '已冻结',
      EXPIRED: '已过期', UNPAID: '未缴费', PAID: '已缴清', WAIVED: '已免除',
      READ: '已读', SENT: '未读', ADMIN: '管理员', LIBRARIAN: '馆员', MEMBER: '读者', VISITOR: '访客',
      true: '是', false: '否',
    },
    en: {
      ACTIVE: 'Active', AVAILABLE: 'Available', ON_LOAN: 'On Loan', MAINTENANCE: 'Under Maintenance', LOST: 'Lost',
      REMOVED: 'Removed', RETURNED: 'Returned', QUEUED: 'Queued', READY_FOR_PICKUP: 'Ready for Pickup',
      COMPLETED: 'Completed', CANCELLED: 'Cancelled', PENDING: 'Pending', FROZEN: 'Frozen',
      EXPIRED: 'Expired', UNPAID: 'Unpaid', PAID: 'Paid', WAIVED: 'Waived',
      READ: 'Read', SENT: 'Unread', ADMIN: 'Administrator', LIBRARIAN: 'Librarian', MEMBER: 'Reader', VISITOR: 'Visitor',
      true: 'Yes', false: 'No',
    },
  };

  const actionLabels = {
    'zh-CN': { BOOK_CREATE: '图书创建', BOOK_UPDATE: '图书更新', COPY_CREATE: '馆藏副本创建', COPY_UPDATE: '馆藏副本更新', COPY_STATUS_CHANGE: '馆藏副本状态变更', MEMBER_APPROVE: '会员审核通过', MEMBER_FREEZE: '会员冻结', MEMBER_UNFREEZE: '会员解冻', MEMBER_RENEW: '会员续期', USER_ROLE_UPDATE: '角色调整', LOAN_CHECKOUT: '借书办理', LOAN_CHECKIN: '还书办理', FINE_GENERATE: '罚款生成', FINE_UPDATE: '罚款更新', FINE_MARK_PAID: '罚款处理', ANNOUNCEMENT_CREATE: '公告创建', ANNOUNCEMENT_UPDATE: '公告更新', POLICY_UPDATE: '提醒策略更新' },
    en: { BOOK_CREATE: 'Book Created', BOOK_UPDATE: 'Book Updated', COPY_CREATE: 'Copy Created', COPY_UPDATE: 'Copy Updated', COPY_STATUS_CHANGE: 'Copy Status Updated', MEMBER_APPROVE: 'Member Approved', MEMBER_FREEZE: 'Member Frozen', MEMBER_UNFREEZE: 'Member Unfrozen', MEMBER_RENEW: 'Membership Renewed', USER_ROLE_UPDATE: 'Role Updated', LOAN_CHECKOUT: 'Checkout Processed', LOAN_CHECKIN: 'Check-in Processed', FINE_GENERATE: 'Fine Generated', FINE_UPDATE: 'Fine Updated', FINE_MARK_PAID: 'Fine Handled', ANNOUNCEMENT_CREATE: 'Notice Created', ANNOUNCEMENT_UPDATE: 'Notice Updated', POLICY_UPDATE: 'Reminder Policy Updated' },
  };

  const targetTypeLabels = {
    'zh-CN': { member: '会员', user: '账号', book: '图书', copy: '馆藏副本', loan: '借阅记录', fine: '罚款记录', announcement: '公告', reminder_policy: '提醒策略' },
    en: { member: 'Member', user: 'Account', book: 'Book', copy: 'Library Copy', loan: 'Loan Record', fine: 'Fine Record', announcement: 'Notice', reminder_policy: 'Reminder Policy' },
  };

  const auditFieldLabels = {
    'zh-CN': { id: '编号', isbn: 'ISBN', title: '标题', author: '作者', category: '分类', description: '简介', publish_year: '出版年份', damaged_compensation_amount: '破损赔偿', lost_compensation_amount: '遗失赔偿', cover_image_url: '封面图片', is_active: '是否启用', actor_user_id: '操作者编号', target_type: '对象类型', target_id: '对象编号', user_id: '读者编号', book_id: '图书编号', copy_id: '馆藏副本编号', loan_id: '借阅编号', status: '状态', role: '角色', amount: '金额', currency: '币种', reason: '原因' },
    en: { id: 'ID', isbn: 'ISBN', title: 'Title', author: 'Author', category: 'Category', description: 'Description', publish_year: 'Publication Year', damaged_compensation_amount: 'Damaged Compensation', lost_compensation_amount: 'Lost Compensation', cover_image_url: 'Cover Image', is_active: 'Enabled', actor_user_id: 'Operator ID', target_type: 'Object Type', target_id: 'Object ID', user_id: 'Reader ID', book_id: 'Book ID', copy_id: 'Copy ID', loan_id: 'Loan ID', status: 'Status', role: 'Role', amount: 'Amount', currency: 'Currency', reason: 'Reason' },
  };

  function getLang() {
    const value = localStorage.getItem(storageKey) || defaultLang;
    return supportedLangs.includes(value) ? value : defaultLang;
  }

  function preserveWhitespace(original, translated) {
    const leading = original.match(/^\s*/)?.[0] || '';
    const trailing = original.match(/\s*$/)?.[0] || '';
    return `${leading}${translated}${trailing}`;
  }

  function translateText(text, lang = getLang()) {
    if (!text || lang === defaultLang) return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (exactTranslations.en[trimmed]) {
      return preserveWhitespace(text, exactTranslations.en[trimmed]);
    }
    const statusEntry = Object.entries(statusLabels[defaultLang]).find(([, value]) => value === trimmed);
    if (statusEntry) {
      return preserveWhitespace(text, statusLabels.en[statusEntry[0]] || trimmed);
    }
    const actionEntry = Object.entries(actionLabels[defaultLang]).find(([, value]) => value === trimmed);
    if (actionEntry) {
      return preserveWhitespace(text, actionLabels.en[actionEntry[0]] || trimmed);
    }
    const targetTypeEntry = Object.entries(targetTypeLabels[defaultLang]).find(([, value]) => value === trimmed);
    if (targetTypeEntry) {
      return preserveWhitespace(text, targetTypeLabels.en[targetTypeEntry[0]] || trimmed);
    }
    const auditFieldEntry = Object.entries(auditFieldLabels[defaultLang]).find(([, value]) => value === trimmed);
    if (auditFieldEntry) {
      return preserveWhitespace(text, auditFieldLabels.en[auditFieldEntry[0]] || trimmed);
    }
    for (const item of phraseReplacements) {
      const match = trimmed.match(item.pattern);
      if (match) {
        return preserveWhitespace(text, item.translate(...match));
      }
    }
    return text;
  }

  function t(key, vars = {}) {
    const base = getLang() === defaultLang ? key : (exactTranslations.en[key] || key);
    return String(base).replace(/\{(\w+)\}/g, (_, varName) => vars[varName] ?? `{${varName}}`);
  }

  function labelForStatus(status, langAware = true) {
    if (!langAware) return status;
    const lang = getLang();
    return statusLabels[lang][status] || statusLabels[defaultLang][status] || status || '';
  }

  function labelForAction(action) {
    const lang = getLang();
    return actionLabels[lang][action] || actionLabels[defaultLang][action] || action || '';
  }

  function labelForTargetType(targetType) {
    const lang = getLang();
    return targetTypeLabels[lang][targetType] || targetTypeLabels[defaultLang][targetType] || targetType || '';
  }

  function labelForAuditField(field) {
    const lang = getLang();
    return auditFieldLabels[lang][field] || auditFieldLabels[defaultLang][field] || field || '';
  }

  function translateAuditValue(value, key = '') {
    if (Array.isArray(value)) {
      return value.map((item) => translateAuditValue(item, key));
    }
    if (value && typeof value === 'object') {
      return Object.fromEntries(
        Object.entries(value).map(([nextKey, nextValue]) => [labelForAuditField(nextKey), translateAuditValue(nextValue, nextKey)])
      );
    }
    if (typeof value === 'string') {
      if (key === 'action') return labelForAction(value);
      if (key === 'target_type' || key === 'type') return labelForTargetType(value);
      if (key === 'role' || key === 'status') return labelForStatus(value);
      return translateText(value);
    }
    if (typeof value === 'boolean') {
      return labelForStatus(String(value));
    }
    return value;
  }

  function getAttributeBucket(element) {
    if (!originalAttributes.has(element)) {
      originalAttributes.set(element, {});
    }
    return originalAttributes.get(element);
  }

  function applyAttributeTranslation(element, attributeName) {
    const currentValue = element.getAttribute(attributeName);
    if (currentValue === null) return;
    const bucket = getAttributeBucket(element);
    if (!(attributeName in bucket)) {
      bucket[attributeName] = currentValue;
    }
    element.setAttribute(attributeName, translateText(bucket[attributeName]));
  }

  function shouldSkipNode(node) {
    const parent = node.parentElement;
    if (!parent) return true;
    if (parent.closest('[data-i18n-skip="true"]')) return true;
    if (['SCRIPT', 'STYLE', 'TEXTAREA'].includes(parent.tagName)) return true;
    return false;
  }

  function applyTextNodeTranslation(node) {
    if (shouldSkipNode(node)) return;
    if (!originalTextNodes.has(node)) {
      originalTextNodes.set(node, node.textContent);
    }
    node.textContent = translateText(originalTextNodes.get(node));
  }

  function applySubtree(root) {
    if (!root) return;
    const base = root.nodeType === Node.ELEMENT_NODE ? root : root.parentElement;
    if (base) {
      [base, ...base.querySelectorAll('*')].forEach((element) => {
        applyAttributeTranslation(element, 'placeholder');
        applyAttributeTranslation(element, 'title');
        applyAttributeTranslation(element, 'aria-label');
      });
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let current;
    while ((current = walker.nextNode())) {
      applyTextNodeTranslation(current);
    }
  }

  function refreshSwitchState() {
    const currentLang = getLang();
    document.querySelectorAll('[data-lang-switch]').forEach((button) => {
      const isActive = button.getAttribute('data-lang-switch') === currentLang;
      button.classList.toggle('lang-switch__button--active', isActive);
      button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function applyDocument() {
    document.documentElement.lang = getLang() === 'en' ? 'en' : 'zh-CN';
    const titleElement = document.querySelector('title');
    if (titleElement) {
      if (originalTitle === null) {
        originalTitle = titleElement.textContent;
      }
      titleElement.textContent = translateText(originalTitle);
    }
    applySubtree(document.body);
    refreshSwitchState();
  }

  function setLang(lang) {
    const nextLang = supportedLangs.includes(lang) ? lang : defaultLang;
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;
    const maxScrollBefore = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    const wasNearBottom = maxScrollBefore - scrollY <= 48;
    const scrollRatio = maxScrollBefore > 0 ? scrollY / maxScrollBefore : 0;

    function restoreScroll() {
      if (wasNearBottom) {
        const maxScrollAfter = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        window.scrollTo(scrollX, maxScrollAfter);
      } else {
        const maxScrollAfter = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        window.scrollTo(scrollX, Math.round(maxScrollAfter * scrollRatio));
      }
    }

    function scheduleRestore() {
      [0, 80, 240, 480, 960, 1440].forEach((delay) => {
        if (delay === 0) {
          requestAnimationFrame(restoreScroll);
          return;
        }
        setTimeout(restoreScroll, delay);
      });
    }

    localStorage.setItem(storageKey, nextLang);
    applyDocument();
    window.dispatchEvent(new CustomEvent('library-lang-changed', { detail: { lang: nextLang } }));
    scheduleRestore();
  }

  function initObserver() {
    if (observer) observer.disconnect();
    observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'characterData') {
          applySubtree(mutation.target);
          return;
        }
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.TEXT_NODE || node.nodeType === Node.ELEMENT_NODE) {
            applySubtree(node);
          }
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function init() {
    document.querySelectorAll('[data-lang-switch]').forEach((button) => {
      button.addEventListener('click', () => setLang(button.getAttribute('data-lang-switch')));
    });
    refreshSwitchState();
    applyDocument();
    initObserver();
  }

  window.LibraryI18n = {
    defaultLang,
    getLang,
    setLang,
    t,
    translateText,
    applySubtree,
    labelForStatus,
    labelForAction,
    labelForTargetType,
    labelForAuditField,
    translateAuditValue,
    init,
  };
})();

window.LibraryI18n.init();

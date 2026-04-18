(() => {
        const apiBase = window.LibraryConfig?.apiBase || '';
        if (!apiBase || window.__libraryFetchPatched) {
          return;
        }

        const nativeFetch = window.fetch.bind(window);
        window.fetch = (input, init = {}) => {
          let nextInput = input;
          if (typeof input === 'string' && input.startsWith('/')) {
            nextInput = `${apiBase}${input}`;
          }
          return nativeFetch(nextInput, {
            ...init,
            credentials: 'include',
          });
        };
        window.__libraryFetchPatched = true;
      })();
window.LibraryAuth = {
        ready: Promise.resolve(false),
        sessionChecked: false,
        sessionValid: false,
        getRole() {
          return localStorage.getItem('library_auth_role') || localStorage.getItem('library_admin_role');
        },
        hasVerifiedSession() {
          return this.sessionChecked && this.sessionValid;
        },
        clearStoredSession() {
          [
            'library_member_token',
            'library_admin_token',
            'library_admin_role',
            'library_auth_name',
            'library_auth_role',
          ].forEach((key) => localStorage.removeItem(key));
        },
        getAdminRole() {
          const role = this.getRole();
          return ['ADMIN', 'LIBRARIAN'].includes(role) ? role : null;
        },
        getReaderToken() {
          const memberToken = localStorage.getItem('library_member_token');
          if (memberToken) {
            return memberToken;
          }
          if (this.getRole() === 'ADMIN') {
            return localStorage.getItem('library_admin_token');
          }
          return null;
        },
        getAdminToken() {
          if (this.getAdminRole()) {
            return localStorage.getItem('library_admin_token');
          }
          return null;
        },
        getReaderHeaders() {
          const token = this.getReaderToken();
          return token ? { Authorization: `Bearer ${token}` } : {};
        },
        getAdminHeaders() {
          const token = this.getAdminToken();
          return token ? { Authorization: `Bearer ${token}` } : {};
        },
        canUseMemberPortal() {
          return ['MEMBER', 'ADMIN'].includes(this.getRole());
        },
        canUseAdminPortal() {
          return ['ADMIN', 'LIBRARIAN'].includes(this.getRole());
        },
        isAdmin() {
          return this.getRole() === 'ADMIN';
        },
        async syncSession() {
          const authName = localStorage.getItem('library_auth_name');
          try {
            const response = await fetch('/me', { credentials: 'same-origin' });
            if (!response.ok) {
              this.sessionChecked = true;
              this.sessionValid = false;
              this.clearStoredSession();
              return false;
            }

            const payload = await response.json();
            const role = payload?.data?.role;
            const displayName =
              payload?.data?.profile?.full_name ||
              payload?.data?.email ||
              authName ||
              '';

            if (!role) {
              this.sessionChecked = true;
              this.sessionValid = false;
              this.clearStoredSession();
              return false;
            }

            localStorage.setItem('library_auth_name', displayName);
            localStorage.setItem('library_auth_role', role);
            if (['ADMIN', 'LIBRARIAN'].includes(role)) {
              localStorage.setItem('library_admin_role', role);
            } else {
              localStorage.removeItem('library_admin_role');
            }
            this.sessionChecked = true;
            this.sessionValid = true;
            return true;
          } catch {
            this.sessionChecked = true;
            this.sessionValid = false;
            this.clearStoredSession();
            return false;
          }
        },
      };

      window.LibraryUi = (() => {
        const errorMessages = {
          EMAIL_EXISTS: {
            title: '这个邮箱已经注册过了',
            description: '可以直接登录，或换一个邮箱继续注册。',
          },
          INVALID_CREDENTIALS: {
            title: '登录状态已失效',
            description: '请重新登录后再继续操作。',
          },
          TOKEN_EXPIRED: {
            title: '登录已过期',
            description: '为了保护账号安全，请重新登录。',
          },
          FORBIDDEN_ROLE: {
            title: '当前账号暂时不能执行这个操作',
            description: '请确认你进入的是正确功能页，或切换账号后重试。',
          },
          MEMBERSHIP_PENDING: {
            title: '账号还在审核中',
            description: '审核通过后才能借阅和预约图书。',
          },
          MEMBERSHIP_FROZEN: {
            title: '账号已被冻结',
            description: '请联系管理员处理后再继续借阅。',
          },
          MEMBERSHIP_EXPIRED: {
            title: '借阅权限已过期',
            description: '请先续期，再继续借阅或预约。',
          },
          BORROW_LIMIT_REACHED: {
            title: '已达到借阅上限',
            description: '可以先归还部分图书后再借新书。',
          },
          NO_AVAILABLE_COPY: {
            title: '这本书目前都借出了',
            description: '可以稍后再试，或先提交预约。',
          },
          COPY_NOT_AVAILABLE: {
            title: '这本书刚刚被借走了',
            description: '请刷新后查看最新馆藏状态。',
          },
          LOAN_NOT_FOUND: {
            title: '没有找到这条借阅记录',
            description: '请确认输入的借阅编号是否正确。',
          },
          LOAN_ALREADY_RETURNED: {
            title: '这本书已经归还',
            description: '无需重复办理归还或续借。',
          },
          COPY_STATE_INVALID: {
            title: '归还状态无效',
            description: '请重新选择归还结果后再提交。',
          },
          RENEWAL_LIMIT_REACHED: {
            title: '这本书不能再续借了',
            description: '已经达到续借次数上限。',
          },
          RENEWAL_BLOCKED_BY_RESERVATION: {
            title: '暂时不能续借',
            description: '这本书后面还有其他读者预约排队。',
          },
          RESERVED_FOR_OTHER_USER: {
            title: '这本书已为其他读者保留',
            description: '请换一本书，或等待馆藏状态更新。',
          },
          RESERVATION_ALREADY_EXISTS: {
            title: '你已经预约过这本书了',
            description: '可前往“我的预约”查看当前排队状态。',
          },
          RESERVATION_NOT_FOUND: {
            title: '没有找到这条预约记录',
            description: '请确认输入的预约编号是否正确。',
          },
          RESERVATION_NOT_CANCELLABLE: {
            title: '当前预约状态不能取消',
            description: '这条预约可能已经完成、过期或被取消。',
          },
          VALIDATION_ERROR: {
            title: '输入内容还不完整',
            description: '请检查必填项后再提交。',
          },
          CONFLICT: {
            title: '操作冲突',
            description: '系统状态刚刚发生变化，请刷新后重试。',
          },
          NOT_FOUND: {
            title: '没有找到对应内容',
            description: '请检查输入信息，或换一个条件再试。',
          },
          HTTP_ERROR: {
            title: '服务器返回了无法识别的结果',
            description: '请稍后重试；如果问题持续出现，再联系管理员。',
          },
          INTERNAL_SERVER_ERROR: {
            title: '服务器暂时出了点问题',
            description: '请稍后再试；如果多次出现同样问题，再联系管理员处理。',
          },
        };

        const statusLabels = {
          ACTIVE: '进行中',
          AVAILABLE: '可借',
          ON_LOAN: '外借中',
          MAINTENANCE: '维修中',
          LOST: '已丢失',
          REMOVED: '已下架',
          RETURNED: '已归还',
          QUEUED: '排队中',
          READY_FOR_PICKUP: '可取书',
          COMPLETED: '已完成',
          CANCELLED: '已取消',
          PENDING: '待处理',
          FROZEN: '已冻结',
          EXPIRED: '已过期',
          UNPAID: '未缴费',
          PAID: '已缴清',
          WAIVED: '已免除',
          READ: '已读',
          SENT: '未读',
          ADMIN: '管理员',
          LIBRARIAN: '馆员',
          MEMBER: '读者',
          VISITOR: '访客',
        };

        const statusTones = {
          ACTIVE: 'success',
          AVAILABLE: 'success',
          ON_LOAN: 'warning',
          MAINTENANCE: 'warning',
          LOST: 'danger',
          REMOVED: 'neutral',
          RETURNED: 'neutral',
          QUEUED: 'warning',
          READY_FOR_PICKUP: 'success',
          COMPLETED: 'success',
          CANCELLED: 'neutral',
          PENDING: 'warning',
          FROZEN: 'danger',
          EXPIRED: 'warning',
          UNPAID: 'warning',
          PAID: 'success',
          WAIVED: 'info',
          READ: 'neutral',
          SENT: 'info',
          ADMIN: 'info',
          LIBRARIAN: 'info',
          MEMBER: 'success',
          VISITOR: 'neutral',
        };

        const htmlMap = {
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;',
        };

        function escapeHtml(value) {
          return String(value ?? '').replace(/[&<>"']/g, (char) => htmlMap[char]);
        }

        function safeText(value, fallback = window.LibraryI18n.t('暂无')) {
          if (value === null || value === undefined || value === '') {
            return fallback;
          }
          return String(value);
        }

        function formatDateTime(value) {
          if (!value) {
            return window.LibraryI18n.t('暂无');
          }
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) {
            return safeText(value);
          }
          return date.toLocaleString(window.LibraryI18n.getLang() === 'en' ? 'en-US' : 'zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          });
        }

        function formatDate(value) {
          if (!value) {
            return window.LibraryI18n.t('暂无');
          }
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) {
            return safeText(value);
          }
          return date.toLocaleDateString(window.LibraryI18n.getLang() === 'en' ? 'en-US' : 'zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
          });
        }

        function toneForStatus(status) {
          return statusTones[status] || 'info';
        }

        function labelForStatus(status) {
          return window.LibraryI18n.labelForStatus(status) || statusLabels[status] || safeText(status, window.LibraryI18n.t('未知状态'));
        }

        function badge(label, tone = 'neutral') {
          return `<span class="result-badge result-badge--${escapeHtml(tone)}">${escapeHtml(window.LibraryI18n.translateText(label))}</span>`;
        }

        function statusBadge(status) {
          return badge(labelForStatus(status), toneForStatus(status));
        }

        function statusList(values = []) {
          return values.filter(Boolean).map((value) => labelForStatus(value)).join(window.LibraryI18n.getLang() === 'en' ? ', ' : '、');
        }

        function actionLinks(actions = []) {
          if (!actions.length) {
            return '';
          }
          return `
            <div class="result-actions">
              ${actions
                .map((action) => `<a class="soft-link" href="${escapeHtml(action.href)}">${escapeHtml(window.LibraryI18n.translateText(action.label))}</a>`)
                .join('')}
            </div>
          `;
        }

        function banner({ tone = 'info', title, description = '', meta = '', actions = [] }) {
          return `
            <section class="feedback-banner feedback-banner--${escapeHtml(tone)}">
              <div class="feedback-banner__title">${escapeHtml(window.LibraryI18n.translateText(title))}</div>
              ${description ? `<p class="feedback-banner__description">${escapeHtml(window.LibraryI18n.translateText(description))}</p>` : ''}
              ${meta ? `<p class="feedback-banner__meta">${escapeHtml(window.LibraryI18n.translateText(meta))}</p>` : ''}
              ${actionLinks(actions)}
            </section>
          `;
        }

        function empty({ title, description, actions = [] }) {
          return banner({ tone: 'info', title, description, actions });
        }

        function metricGrid(items = []) {
          const validItems = items.filter((item) => item && item.label);
          if (!validItems.length) {
            return '';
          }
          return `
            <div class="result-grid">
              ${validItems
                .map(
                  (item) => `
                    <section class="result-metric">
                      <span class="result-metric__label">${escapeHtml(window.LibraryI18n.translateText(item.label))}</span>
                      <strong class="result-metric__value">${escapeHtml(safeText(item.value, '-'))}</strong>
                    </section>
                  `
                )
                .join('')}
            </div>
          `;
        }

        function infoList(items = []) {
          const validItems = items.filter((item) => item && item.label);
          if (!validItems.length) {
            return '';
          }
          return `
            <div class="info-list">
              ${validItems
                .map(
                  (item) => `
                    <div class="info-list__row">
                      <span class="info-list__label">${escapeHtml(window.LibraryI18n.translateText(item.label))}</span>
                      <strong class="info-list__value">${escapeHtml(safeText(item.value, '-'))}</strong>
                    </div>
                  `
                )
                .join('')}
            </div>
          `;
        }

        function metaList(items = []) {
          const validItems = items.filter(Boolean);
          if (!validItems.length) {
            return '';
          }
          return `
            <div class="result-meta">
              ${validItems.map((item) => `<span>${escapeHtml(window.LibraryI18n.translateText(item))}</span>`).join('')}
            </div>
          `;
        }

        function card({ title, badges = [], meta = [], description = '', details = '', actions = [] }) {
          return `
            <article class="result-card">
              <div class="result-card__header">
                <div>
                  <h3 class="result-card__title">${escapeHtml(window.LibraryI18n.translateText(title))}</h3>
                  ${metaList(meta)}
                </div>
                ${badges.length ? `<div class="result-badges">${badges.join('')}</div>` : ''}
              </div>
              ${description ? `<p class="result-card__description">${escapeHtml(window.LibraryI18n.translateText(description))}</p>` : ''}
              ${details}
              ${actionLinks(actions)}
            </article>
          `;
        }

        function normaliseError(payload) {
          const error = payload?.error || {};
          const mapped = errorMessages[error.code] || {
            title: window.LibraryI18n.t('操作未完成'),
            description: safeText(error.message, window.LibraryI18n.t('请稍后重试。')),
          };

          let description = mapped.description;
          if (Array.isArray(error.details) && error.details.length) {
            const detailText = error.details
              .slice(0, 2)
              .map((item) => item?.msg)
              .filter(Boolean)
              .join('；');
            if (detailText) {
              description = `${description} ${detailText}`;
            }
          }

          return {
            title: mapped.title,
            description,
            requestId: payload?.requestId || '',
          };
        }

        function render(container, html) {
          container.innerHTML = html;
          window.LibraryI18n.applySubtree(container);
        }

        function renderError(container, payload, actions = []) {
          const error = normaliseError(payload);
          render(
            container,
            `<div class="feedback-stack">${banner({
              tone: 'danger',
              title: error.title,
              description: error.description,
              meta: error.requestId ? window.LibraryI18n.t('请求编号：{requestId}', { requestId: error.requestId }) : '',
              actions,
            })}</div>`
          );
        }

        return {
          badge,
          banner,
          card,
          empty,
          escapeHtml,
          formatDate,
          formatDateTime,
          infoList,
          labelForStatus,
          statusList,
          metricGrid,
          render,
          renderError,
          safeText,
          statusBadge,
          t: window.LibraryI18n.t,
        };
      })();

(() => {
        const accessEntry = document.getElementById('access-entry');
        const accountMenu = document.getElementById('account-menu');
        const memberEntry = document.getElementById('member-entry');
        const adminEntry = document.getElementById('admin-entry');
        const logoutEntry = document.getElementById('logout-entry');
        if (!accessEntry || !accountMenu || !memberEntry || !adminEntry || !logoutEntry) return;

        function refreshAccountState() {
          const t = window.LibraryI18n.t;
          if (!window.LibraryAuth.hasVerifiedSession()) {
            accessEntry.textContent = t('登录/注册');
            accessEntry.classList.remove('header-action--account');
            accessEntry.setAttribute('href', '/login');
            accountMenu.classList.add('account-menu--hidden');
            memberEntry.classList.add('account-menu__item--hidden');
            adminEntry.classList.add('account-menu__item--hidden');
            return false;
          }

          const authName = localStorage.getItem('library_auth_name');
          const authRole = localStorage.getItem('library_auth_role');

          if (!authName || !authRole) {
            accessEntry.textContent = t('登录/注册');
            accessEntry.classList.remove('header-action--account');
            accessEntry.setAttribute('href', '/login');
            accountMenu.classList.add('account-menu--hidden');
            memberEntry.classList.add('account-menu__item--hidden');
            adminEntry.classList.add('account-menu__item--hidden');
            return false;
          }

          accessEntry.textContent = authName;
          accessEntry.classList.remove('is-active');
          accessEntry.classList.add('header-action--account');
          accessEntry.setAttribute('href', '#');
          memberEntry.textContent = t('进入读者服务');
          adminEntry.textContent = t('进入管理后台');
          logoutEntry.textContent = t('退出登录');
          memberEntry.classList.toggle('account-menu__item--hidden', !['MEMBER', 'ADMIN'].includes(authRole));
          adminEntry.classList.toggle('account-menu__item--hidden', !['ADMIN', 'LIBRARIAN'].includes(authRole));
          return true;
        }

        accessEntry.addEventListener('click', (event) => {
          if (!refreshAccountState()) return;
          event.preventDefault();
          accountMenu.classList.toggle('account-menu--hidden');
        });

        logoutEntry.addEventListener('click', async () => {
          try {
            await fetch('/auth/logout', {
              method: 'POST',
              credentials: 'same-origin',
            });
          } catch {}
          window.LibraryAuth.clearStoredSession();
          refreshAccountState();
          window.location.href = '/';
        });

        document.addEventListener('click', (event) => {
          if (accountMenu.classList.contains('account-menu--hidden')) return;
          if (!accountMenu.contains(event.target) && !accessEntry.contains(event.target)) {
            accountMenu.classList.add('account-menu--hidden');
          }
        });

        window.addEventListener('library-auth-changed', () => {
          refreshAccountState();
          accountMenu.classList.add('account-menu--hidden');
        });

        refreshAccountState();
        window.LibraryAuth.ready = window.LibraryAuth.syncSession();
        window.LibraryAuth.ready.then(() => {
          refreshAccountState();
          accountMenu.classList.add('account-menu--hidden');
        });
        window.addEventListener('library-lang-changed', () => {
          refreshAccountState();
          accountMenu.classList.add('account-menu--hidden');
        });
      })();


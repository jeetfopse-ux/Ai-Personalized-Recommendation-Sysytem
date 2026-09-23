/**
 * Personal Finance Advisor Bot - Interactive Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  initModals();
  initToastDismissal();
  initMobileNav();
  initCharts();
  initAIChat();
});

/* ==========================================================================
   MODAL CONTROLLER
   ========================================================================== */
function initModals() {
  const openButtons = document.querySelectorAll("[data-modal-target]");
  const closeButtons = document.querySelectorAll(".modal-close, [data-modal-close]");

  openButtons.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute("data-modal-target");
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add("active");
        const firstInput = modal.querySelector("input:not([type=hidden]), select");
        if (firstInput) firstInput.focus();
      }
    });
  });

  closeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal-overlay");
      if (modal) modal.classList.remove("active");
    });
  });

  // Close on outside click
  window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
      e.target.classList.remove("active");
    }
  });

  // Close on Escape key
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay.active").forEach(m => m.classList.remove("active"));
    }
  });
}

/* ==========================================================================
   TOAST NOTIFICATION AUTO-DISMISS
   ========================================================================== */
function initToastDismissal() {
  const toasts = document.querySelectorAll(".toast");
  toasts.forEach(t => {
    setTimeout(() => {
      t.style.opacity = "0";
      t.style.transform = "translateX(100%)";
      t.style.transition = "all 0.3s ease";
      setTimeout(() => t.remove(), 300);
    }, 4500);
  });
}

/* ==========================================================================
   MOBILE NAVIGATION
   ========================================================================== */
function initMobileNav() {
  const menuBtn = document.getElementById("mobile-menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }
}

/* ==========================================================================
   CHART.JS VISUALIZATIONS
   ========================================================================== */
let expenseDonutChart = null;
let trendChart = null;

async function initCharts() {
  const donutCanvas = document.getElementById("categoryExpenseChart");
  const trendCanvas = document.getElementById("cashFlowTrendChart");

  if (!donutCanvas && !trendCanvas) return;

  try {
    const urlParams = new URLSearchParams(window.location.search);
    const year = urlParams.get("year") || "";
    const month = urlParams.get("month") || "";
    
    const response = await fetch(`/api/dashboard/charts?year=${year}&month=${month}`);
    if (!response.ok) return;
    const data = await response.json();

    // 1. Expense Breakdown Donut Chart
    if (donutCanvas && data.category_chart) {
      const ctx = donutCanvas.getContext("2d");
      if (data.category_chart.data.length === 0) {
        // Render empty placeholder
        donutCanvas.parentElement.innerHTML = `
          <div style="height: 260px; display: flex; align-items: center; justify-content: center; flex-direction: column; color: var(--text-muted);">
            <i class="fas fa-receipt" style="font-size: 2rem; margin-bottom: 8px;"></i>
            <p>No expenses recorded for this month.</p>
          </div>
        `;
      } else {
        expenseDonutChart = new Chart(ctx, {
          type: "doughnut",
          data: {
            labels: data.category_chart.labels,
            datasets: [{
              data: data.category_chart.data,
              backgroundColor: data.category_chart.colors,
              borderWidth: 2,
              borderColor: "#111827",
              hoverOffset: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  color: "#cbd5e1",
                  font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                  padding: 14,
                  usePointStyle: true
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || "";
                    const value = context.parsed || 0;
                    return ` ${label}: $${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                  }
                }
              }
            },
            cutout: "68%"
          }
        });
      }
    }

    // 2. 6-Month Income vs Expense Trend Bar Chart
    if (trendCanvas && data.trend_chart) {
      const ctx = trendCanvas.getContext("2d");
      trendChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: data.trend_chart.labels,
          datasets: [
            {
              label: "Income",
              data: data.trend_chart.incomes,
              backgroundColor: "rgba(16, 185, 129, 0.75)",
              borderColor: "#10b981",
              borderWidth: 1,
              borderRadius: 6
            },
            {
              label: "Expenses",
              data: data.trend_chart.expenses,
              backgroundColor: "rgba(239, 68, 68, 0.75)",
              borderColor: "#ef4444",
              borderWidth: 1,
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#94a3b8", font: { family: "'Plus Jakarta Sans', sans-serif" } }
            },
            y: {
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: {
                color: "#94a3b8",
                callback: (val) => `$${val.toLocaleString()}`
              }
            }
          },
          plugins: {
            legend: {
              position: "top",
              labels: {
                color: "#cbd5e1",
                font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                usePointStyle: true
              }
            },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString(undefined, {minimumFractionDigits: 2})}`
              }
            }
          }
        }
      });
    }

  } catch (err) {
    console.error("Error loading charts:", err);
  }
}

/* ==========================================================================
   AI FINANCIAL ADVISOR CHAT
   ========================================================================== */
function initAIChat() {
  const chatForm = document.getElementById("ai-chat-form");
  const chatInput = document.getElementById("ai-chat-input");
  const messagesContainer = document.getElementById("chat-messages-container");
  const clearBtn = document.getElementById("clear-chat-btn");
  const chipButtons = document.querySelectorAll(".chip-btn");

  if (!chatForm || !chatInput || !messagesContainer) return;

  // Scroll to bottom on load
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Quick chip click
  chipButtons.forEach(chip => {
    chip.addEventListener("click", () => {
      chatInput.value = chip.innerText.trim();
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  // Handle Form Submit
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    // Append User Bubble
    appendMessage("user", text);
    chatInput.value = "";
    chatInput.disabled = true;

    // Show Typing Indicator
    const typingIndicator = appendTypingIndicator();
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
      const res = await fetch("/api/advisor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      typingIndicator.remove();

      if (res.ok) {
        const data = await res.json();
        appendMessage("assistant", data.reply);
      } else {
        appendMessage("assistant", "⚠️ Sorry, I encountered an issue processing your request. Please check your AI API key or try again in a moment.");
      }
    } catch (err) {
      typingIndicator.remove();
      appendMessage("assistant", "⚠️ Network error communicating with the financial advisor service.");
    } finally {
      chatInput.disabled = false;
      chatInput.focus();
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  // Clear chat history
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      if (confirm("Clear your AI conversation history?")) {
        await fetch("/api/advisor/chat/clear", { method: "POST" });
        messagesContainer.innerHTML = `
          <div class="chat-bubble assistant">
            <p>👋 Chat history reset. How can I help with your financial goals today?</p>
          </div>
        `;
      }
    });
  }

  function appendMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    
    // Convert newlines and bold markdown
    let formatted = escapeHtml(content)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
      
    bubble.innerHTML = `<p>${formatted}</p>`;
    messagesContainer.appendChild(bubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendTypingIndicator() {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble assistant typing-bubble";
    bubble.innerHTML = `
      <div style="display: flex; gap: 4px; align-items: center; padding: 4px 8px;">
        <span style="animation: pulse 1s infinite;">●</span>
        <span style="animation: pulse 1s infinite 0.2s;">●</span>
        <span style="animation: pulse 1s infinite 0.4s;">●</span>
      </div>
    `;
    messagesContainer.appendChild(bubble);
    return bubble;
  }

  function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
  }
}

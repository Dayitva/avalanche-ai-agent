// Update wallet balance
function updateWalletBalance() {
    fetch('/api/wallet/balance')
        .then(response => response.json())
        .then(data => {
            document.getElementById('wallet-balance').textContent = 
                parseFloat(data.balance).toFixed(4);
        })
        .catch(error => console.error('Error fetching balance:', error));
}

// Update recent transactions
function updateTransactions() {
    fetch('/api/transactions/recent')
        .then(response => response.json())
        .then(transactions => {
            const transactionsTable = document.getElementById('transactions-table');
            if (transactionsTable) {
                transactionsTable.innerHTML = transactions.map(tx => `
                    <tr>
                        <td>${tx.hash.substring(0, 8)}...</td>
                        <td>${tx.type}</td>
                        <td>${parseFloat(tx.amount).toFixed(4)}</td>
                        <td>
                            <span class="badge bg-${tx.status === 'success' ? 'success' : 'danger'}">
                                ${tx.status}
                            </span>
                        </td>
                        <td>${new Date(tx.timestamp).toLocaleString()}</td>
                    </tr>
                `).join('');
            }

            const recentTransactions = document.getElementById('recent-transactions');
            if (recentTransactions) {
                recentTransactions.innerHTML = transactions.slice(0, 5).map(tx => `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>${tx.type}</span>
                        <span>${parseFloat(tx.amount).toFixed(4)} AVAX</span>
                    </div>
                `).join('');
            }
        })
        .catch(error => console.error('Error fetching transactions:', error));
}

// Initialize performance chart
function initializeChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 7}, (_, i) => 
                new Date(Date.now() - (6-i) * 24*60*60*1000).toLocaleDateString()
            ),
            datasets: [{
                label: 'Portfolio Value (AVAX)',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    updateWalletBalance();
    updateTransactions();
    initializeChart();
    
    // Refresh data every 30 seconds
    setInterval(() => {
        updateWalletBalance();
        updateTransactions();
    }, 30000);
});

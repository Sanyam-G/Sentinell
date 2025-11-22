const express = require('express');
const app = express();
const PORT = process.env.PORT || 3002;

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'payment-service' });
});

// Payment charge endpoint
app.post('/charge', (req, res) => {
  const { amount, currency, token } = req.body;

  console.log(`Processing payment: ${amount} ${currency}`);

  if (!amount || !currency || !token) {
    return res.status(400).json({
      error: 'Missing required fields',
      required: ['amount', 'currency', 'token']
    });
  }

  // Simulate payment processing
  setTimeout(() => {
    res.json({
      success: true,
      transactionId: `txn_${Date.now()}`,
      amount,
      currency,
      timestamp: new Date().toISOString()
    });
  }, 100);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Payment Service running on port ${PORT}`);
});

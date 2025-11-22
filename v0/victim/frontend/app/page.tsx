'use client'

import { useState, useEffect } from 'react'

interface Product {
  id: number
  name: string
  price: number
  description: string
  stock: number
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cart, setCart] = useState<{ [key: number]: number }>({})
  const [checkoutStatus, setCheckoutStatus] = useState<string | null>(null)

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      const res = await fetch('/api/products')
      if (!res.ok) throw new Error('Failed to fetch products')
      const data = await res.json()
      setProducts(data.products)
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }

  const addToCart = (productId: number) => {
    setCart(prev => ({
      ...prev,
      [productId]: (prev[productId] || 0) + 1
    }))
  }

  const getTotalAmount = () => {
    return Object.entries(cart).reduce((total, [productId, quantity]) => {
      const product = products.find(p => p.id === Number(productId))
      return total + (product?.price || 0) * quantity
    }, 0)
  }

  const handleCheckout = async () => {
    const totalAmount = getTotalAmount()
    if (totalAmount === 0) {
      setCheckoutStatus('Cart is empty')
      return
    }

    setCheckoutStatus('Processing...')
    try {
      const res = await fetch('/api/charge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: totalAmount,
          currency: 'USD',
          token: 'tok_demo_' + Date.now()
        })
      })

      if (!res.ok) throw new Error('Payment failed')
      const data = await res.json()
      setCheckoutStatus(`Success! Transaction ID: ${data.transactionId}`)
      setCart({})
    } catch (err) {
      setCheckoutStatus('Payment failed - please try again')
    }
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading products...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Error: {error}</div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>CloudOps Store</h1>
        <p style={styles.subtitle}>Enterprise Cloud Operations Tools</p>
      </header>

      <div style={styles.productGrid}>
        {products.map(product => (
          <div key={product.id} style={styles.productCard}>
            <h3 style={styles.productName}>{product.name}</h3>
            <p style={styles.productDescription}>{product.description}</p>
            <p style={styles.productPrice}>${product.price.toFixed(2)}</p>
            <p style={styles.productStock}>Stock: {product.stock}</p>
            <button
              onClick={() => addToCart(product.id)}
              style={styles.addButton}
            >
              Add to Cart {cart[product.id] ? `(${cart[product.id]})` : ''}
            </button>
          </div>
        ))}
      </div>

      {Object.keys(cart).length > 0 && (
        <div style={styles.cartSection}>
          <h2 style={styles.cartTitle}>Cart</h2>
          <p style={styles.cartTotal}>Total: ${getTotalAmount().toFixed(2)}</p>
          <button onClick={handleCheckout} style={styles.checkoutButton}>
            Checkout
          </button>
          {checkoutStatus && (
            <p style={styles.checkoutStatus}>{checkoutStatus}</p>
          )}
        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    backgroundColor: '#0a0a0a',
    color: '#ffffff'
  },
  header: {
    textAlign: 'center' as const,
    marginBottom: '40px',
    paddingTop: '20px'
  },
  title: {
    fontSize: '48px',
    fontWeight: 'bold',
    margin: '0',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text'
  },
  subtitle: {
    fontSize: '18px',
    color: '#999',
    marginTop: '10px'
  },
  loading: {
    textAlign: 'center' as const,
    padding: '100px',
    fontSize: '24px'
  },
  error: {
    textAlign: 'center' as const,
    padding: '100px',
    fontSize: '24px',
    color: '#ff4444'
  },
  productGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '20px',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  productCard: {
    backgroundColor: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '12px',
    padding: '24px',
    transition: 'transform 0.2s, box-shadow 0.2s'
  },
  productName: {
    fontSize: '22px',
    fontWeight: 'bold',
    marginBottom: '12px',
    color: '#ffffff'
  },
  productDescription: {
    fontSize: '14px',
    color: '#999',
    marginBottom: '16px',
    lineHeight: '1.5'
  },
  productPrice: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: '8px'
  },
  productStock: {
    fontSize: '13px',
    color: '#666',
    marginBottom: '16px'
  },
  addButton: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  cartSection: {
    position: 'fixed' as const,
    bottom: '0',
    left: '0',
    right: '0',
    backgroundColor: '#1a1a1a',
    borderTop: '2px solid #667eea',
    padding: '20px',
    textAlign: 'center' as const
  },
  cartTitle: {
    fontSize: '24px',
    marginBottom: '10px'
  },
  cartTotal: {
    fontSize: '20px',
    color: '#667eea',
    marginBottom: '15px'
  },
  checkoutButton: {
    padding: '15px 40px',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '18px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  checkoutStatus: {
    marginTop: '15px',
    fontSize: '16px',
    color: '#10b981'
  }
}

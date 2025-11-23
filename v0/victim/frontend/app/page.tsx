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
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // Check system preference and localStorage
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark)
    setIsDark(shouldBeDark)
    document.documentElement.classList.toggle('dark', shouldBeDark)
  }, [])

  const toggleTheme = () => {
    const newTheme = !isDark
    setIsDark(newTheme)
    localStorage.setItem('theme', newTheme ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', newTheme)
  }

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
    <div style={isDark ? styles.containerDark : styles.containerLight}>
      <header style={styles.header}>
        <div style={styles.headerTop}>
          <div>
            <h1 style={styles.title}>CloudOps Store</h1>
            <p style={isDark ? styles.subtitleDark : styles.subtitleLight}>Enterprise Cloud Operations Tools</p>
          </div>
          <button onClick={toggleTheme} style={styles.themeToggle}>
            {isDark ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <div style={styles.productGrid}>
        {products.map(product => (
          <div key={product.id} style={isDark ? styles.productCardDark : styles.productCardLight}>
            <h3 style={isDark ? styles.productNameDark : styles.productNameLight}>{product.name}</h3>
            <p style={isDark ? styles.productDescriptionDark : styles.productDescriptionLight}>{product.description}</p>
            <p style={styles.productPrice}>${product.price.toFixed(2)}</p>
            <p style={isDark ? styles.productStockDark : styles.productStockLight}>Stock: {product.stock}</p>
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
        <div style={isDark ? styles.cartSectionDark : styles.cartSectionLight}>
          <h2 style={isDark ? styles.cartTitleDark : styles.cartTitleLight}>Cart</h2>
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
  containerLight: {
    minHeight: '100vh',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    backgroundColor: '#ffffff',
    color: '#1a1a1a',
    transition: 'all 0.3s ease'
  },
  containerDark: {
    minHeight: '100vh',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    backgroundColor: '#0f172a',
    color: '#ffffff',
    transition: 'all 0.3s ease'
  },
  header: {
    textAlign: 'center' as const,
    marginBottom: '40px',
    paddingTop: '20px'
  },
  headerTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  title: {
    fontSize: '48px',
    fontWeight: 'bold',
    margin: '0',
    color: '#3b82f6'
  },
  subtitleLight: {
    fontSize: '18px',
    color: '#64748b',
    marginTop: '10px'
  },
  subtitleDark: {
    fontSize: '18px',
    color: '#94a3b8',
    marginTop: '10px'
  },
  themeToggle: {
    width: '50px',
    height: '50px',
    fontSize: '24px',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    backgroundColor: 'transparent',
    transition: 'all 0.2s ease'
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
    color: '#ef4444'
  },
  productGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '24px',
    maxWidth: '1200px',
    margin: '0 auto',
    paddingBottom: '120px'
  },
  productCardLight: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    transition: 'all 0.2s ease'
  },
  productCardDark: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
    transition: 'all 0.2s ease'
  },
  productNameLight: {
    fontSize: '22px',
    fontWeight: 'bold',
    marginBottom: '12px',
    color: '#1a1a1a'
  },
  productNameDark: {
    fontSize: '22px',
    fontWeight: 'bold',
    marginBottom: '12px',
    color: '#ffffff'
  },
  productDescriptionLight: {
    fontSize: '14px',
    color: '#64748b',
    marginBottom: '16px',
    lineHeight: '1.5'
  },
  productDescriptionDark: {
    fontSize: '14px',
    color: '#94a3b8',
    marginBottom: '16px',
    lineHeight: '1.5'
  },
  productPrice: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: '8px'
  },
  productStockLight: {
    fontSize: '13px',
    color: '#94a3b8',
    marginBottom: '16px'
  },
  productStockDark: {
    fontSize: '13px',
    color: '#64748b',
    marginBottom: '16px'
  },
  addButton: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  },
  cartSectionLight: {
    position: 'fixed' as const,
    bottom: '0',
    left: '0',
    right: '0',
    backgroundColor: '#ffffff',
    borderTop: '2px solid #e2e8f0',
    padding: '20px',
    textAlign: 'center' as const,
    boxShadow: '0 -4px 6px rgba(0,0,0,0.05)'
  },
  cartSectionDark: {
    position: 'fixed' as const,
    bottom: '0',
    left: '0',
    right: '0',
    backgroundColor: '#1e293b',
    borderTop: '2px solid #334155',
    padding: '20px',
    textAlign: 'center' as const,
    boxShadow: '0 -4px 6px rgba(0,0,0,0.3)'
  },
  cartTitleLight: {
    fontSize: '24px',
    marginBottom: '10px',
    color: '#1a1a1a'
  },
  cartTitleDark: {
    fontSize: '24px',
    marginBottom: '10px',
    color: '#ffffff'
  },
  cartTotal: {
    fontSize: '20px',
    color: '#3b82f6',
    marginBottom: '15px',
    fontWeight: 'bold'
  },
  checkoutButton: {
    padding: '15px 40px',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '18px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  },
  checkoutStatus: {
    marginTop: '15px',
    fontSize: '16px',
    color: '#10b981'
  }
}

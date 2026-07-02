type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'outline' | 'danger'
}

const variants = {
  primary: 'border-octo-secondary bg-octo-secondary text-white hover:bg-octo-success',
  outline: 'border-octo-border bg-transparent text-octo-text-primary hover:border-octo-border-hover hover:bg-octo-elevated',
  danger: 'border-octo-error/50 bg-transparent text-octo-error hover:bg-octo-error/10',
}

export function Button({ className = '', variant = 'primary', ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex h-8 items-center justify-center rounded-octo border px-4 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    />
  )
}

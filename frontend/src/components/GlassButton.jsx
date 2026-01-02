import React from 'react';

const GlassButton = ({
  children,
  variant = "default",
  className = "",
  disabled = false,
  ...props
}) => {
  const baseClasses = "glass-button";

  const variants = {
    default: "glass-button",
    primary: "glass-button-primary",
    secondary: "backdrop-blur-sm bg-white/5 border border-white/20 text-white/80 hover:bg-white/10 hover:border-white/30 hover:text-white",
    danger: "backdrop-blur-sm bg-red-500/20 border border-red-400/30 text-red-300 hover:bg-red-500/30 hover:border-red-400/50 hover:text-red-200"
  };

  const disabledClasses = disabled ? "opacity-50 cursor-not-allowed hover:bg-white/10 hover:border-white/20" : "";

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${disabledClasses} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default GlassButton;

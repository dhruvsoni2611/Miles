import React from 'react';

const GlassCard = ({
  children,
  className = "",
  floating = false,
  hover = true,
  padding = "p-6",
  ...props
}) => {
  const baseClasses = "glass-card";
  const hoverClasses = "";
  const floatingClasses = floating ? "floating-animation hover:scale-105 transition-transform duration-300" : "";

  return (
    <div
      className={`${baseClasses} ${hoverClasses} ${floatingClasses} ${padding} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;

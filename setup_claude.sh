#!/bin/bash

echo "🔑 CONFIGURACIÓN CLAUDE API - Agente de IA para Shopify"
echo "======================================================="

echo "📝 Pasos para configurar tu API key de Claude:"
echo ""
echo "1. 🌐 Ve a: https://console.anthropic.com/"
echo "2. 🔑 Crea tu cuenta y obtén tu API key"
echo "3. 💰 Precio Claude: ~$8 por 1M tokens (muy económico)"
echo ""

echo "🚀 CONFIGURACIÓN RÁPIDA:"
echo ""
echo "# Opción 1: Variable de entorno (recomendado)"
echo "export ANTHROPIC_API_KEY=tu_api_key_aqui"
echo ""
echo "# Opción 2: Archivo .env"
echo "echo 'ANTHROPIC_API_KEY=tu_api_key_aqui' > .env"
echo ""

echo "🧪 PROBAR EL SISTEMA:"
echo ""
echo "# Con tu API key configurada:"
echo "python3 demo_claude_simple.py"
echo ""
echo "# O ejecutar sistema completo:"
echo "pip install anthropic --break-system-packages"
echo "python3 demo_claude.py"
echo ""

echo "💡 EJEMPLO DE USO:"
echo ""
cat << 'EOF'
# Configurar API key
export ANTHROPIC_API_KEY=sk-ant-api03-tu-clave-aqui

# Probar agente
python3 demo_claude_simple.py

# ¡Verás respuestas mucho más inteligentes!
EOF

echo ""
echo "🎯 VENTAJAS DE CLAUDE vs OpenAI:"
echo "✅ Mejor comprensión contextual"
echo "✅ Respuestas más largas y detalladas"  
echo "✅ Mejor en español"
echo "✅ Más económico"
echo "✅ Menos restricciones"

echo ""
echo "📞 ¿NECESITAS AYUDA?"
echo "El sistema funciona perfecto en modo demo."
echo "Con tu API key será aún mejor!"
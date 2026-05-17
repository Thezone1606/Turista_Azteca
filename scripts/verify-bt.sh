#!/usr/bin/env bash
# Verifica que la auto-conexion BT al arranque funciono.
# Uso: ~/turista/scripts/verify-bt.sh

MAC="40:B8:2C:F8:53:80"
ok() { echo -e "  \e[32m✓\e[0m $1"; }
fail() { echo -e "  \e[31m✗\e[0m $1"; FAILED=1; }
FAILED=0

echo "=== 1. Linger del usuario ==="
if loginctl show-user viajeazteca 2>/dev/null | grep -q "Linger=yes"; then
  ok "Linger=yes (user@1000.service arranca al boot)"
else
  fail "Linger NO esta habilitado"
fi

echo "=== 2. Servicio connect-mobo ==="
state=$(systemctl --user is-active connect-mobo.service 2>&1)
if [ "$state" = "active" ]; then
  ok "connect-mobo.service = active"
  systemctl --user status connect-mobo.service --no-pager 2>&1 | grep "Mobo connected" | sed 's/^/    /'
else
  fail "connect-mobo.service estado: $state"
fi

echo "=== 3. Bocina conectada ==="
if bluetoothctl info "$MAC" 2>/dev/null | grep -q "Connected: yes"; then
  ok "Mobo $MAC conectada"
else
  fail "Mobo $MAC NO conectada"
fi

echo "=== 4. Sink default en PipeWire ==="
sink=$(pactl info 2>/dev/null | grep "Default Sink" | awk '{print $3}')
if [[ "$sink" == bluez_output* ]]; then
  ok "Default sink: $sink"
else
  fail "Default sink: $sink (no es BT)"
fi

echo "=== 5. Test de audio ==="
if [ -f ~/turista/audio/bienvenida.mp3 ]; then
  echo "  Reproduciendo bienvenida.mp3..."
  mpg123 -q ~/turista/audio/bienvenida.mp3 2>/dev/null && ok "mp3 reproducido (escucha la bocina)"
else
  fail "Falta ~/turista/audio/bienvenida.mp3"
fi

echo
if [ $FAILED -eq 0 ]; then
  echo -e "\e[32m=== TODO OK ===\e[0m"
  exit 0
else
  echo -e "\e[31m=== HUBO FALLOS ===\e[0m  ver arriba"
  exit 1
fi

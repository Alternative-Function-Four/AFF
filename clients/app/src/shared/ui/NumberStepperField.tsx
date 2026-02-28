import { Pressable, StyleSheet, Text, View } from "react-native";

interface NumberStepperFieldProps {
  label: string;
  value: number;
  onChange: (nextValue: number) => void;
  min: number;
  max: number;
  step?: number;
  hint?: string;
}

export function NumberStepperField({
  label,
  value,
  onChange,
  min,
  max,
  step = 5,
  hint
}: NumberStepperFieldProps): JSX.Element {
  const decDisabled = value <= min;
  const incDisabled = value >= max;

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: decDisabled }}
          style={[styles.stepperBtn, decDisabled ? styles.disabled : undefined]}
          disabled={decDisabled}
          onPress={() => onChange(Math.max(min, value - step))}
        >
          <Text style={styles.btnLabel}>-</Text>
        </Pressable>
        <View style={styles.valueWrap}>
          <Text style={styles.value}>{value}</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: incDisabled }}
          style={[styles.stepperBtn, incDisabled ? styles.disabled : undefined]}
          disabled={incDisabled}
          onPress={() => onChange(Math.min(max, value + step))}
        >
          <Text style={styles.btnLabel}>+</Text>
        </Pressable>
      </View>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 6
  },
  label: {
    color: "#12263A",
    fontWeight: "600"
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  stepperBtn: {
    width: 44,
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center"
  },
  disabled: {
    opacity: 0.5
  },
  btnLabel: {
    color: "#1A3149",
    fontWeight: "700",
    fontSize: 18,
    lineHeight: 18
  },
  valueWrap: {
    flex: 1,
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CCD5E0",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF"
  },
  value: {
    color: "#1A3149",
    fontWeight: "700",
    fontSize: 16
  },
  hint: {
    color: "#607184",
    fontSize: 12
  }
});

import { Pressable, StyleSheet, Text, TextInput, View, type TextInputProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import type { ReactNode } from "react";

type ScreenProps = {
  children: ReactNode;
  eyebrow: string;
  title: string;
};

type FieldProps = TextInputProps & {
  error?: string | undefined;
  label: string;
};

type ActionButtonProps = {
  disabled?: boolean;
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary";
};

export function OnboardingScreen({ children, eyebrow, title }: ScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
        </View>
        {children}
      </View>
    </SafeAreaView>
  );
}

export function Field({ error, label, ...inputProps }: FieldProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor="#64748b"
        style={[styles.input, error ? styles.inputError : null]}
        {...inputProps}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

export function ActionButton({ disabled, label, onPress, variant = "primary" }: ActionButtonProps) {
  const isSecondary = variant === "secondary";

  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        isSecondary ? styles.secondaryButton : styles.primaryButton,
        disabled ? styles.disabled : null,
        pressed ? styles.pressed : null
      ]}
    >
      <Text style={isSecondary ? styles.secondaryButtonText : styles.primaryButtonText}>{label}</Text>
    </Pressable>
  );
}

export function ButtonRow({ children }: { children: ReactNode }) {
  return <View style={styles.buttonRow}>{children}</View>;
}

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  container: {
    flex: 1,
    gap: 22,
    padding: 24
  },
  header: {
    gap: 6
  },
  eyebrow: {
    color: "#15803d",
    fontSize: 13,
    fontWeight: "700",
    textTransform: "uppercase"
  },
  title: {
    color: "#0f172a",
    fontSize: 28,
    fontWeight: "700"
  },
  field: {
    gap: 8
  },
  label: {
    color: "#0f172a",
    fontSize: 14,
    fontWeight: "700"
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    color: "#0f172a",
    fontSize: 16,
    paddingHorizontal: 14
  },
  inputError: {
    borderColor: "#dc2626"
  },
  error: {
    color: "#dc2626",
    fontSize: 13
  },
  button: {
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    paddingHorizontal: 16
  },
  primaryButton: {
    backgroundColor: "#15803d"
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    backgroundColor: "#ffffff"
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700"
  },
  secondaryButtonText: {
    color: "#0f172a",
    fontSize: 15,
    fontWeight: "700"
  },
  pressed: {
    opacity: 0.78
  },
  disabled: {
    opacity: 0.5
  },
  buttonRow: {
    flexDirection: "row",
    gap: 12
  },
  metric: {
    gap: 6,
    borderWidth: 1,
    borderColor: "#e2e8f0",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 16
  },
  metricLabel: {
    color: "#64748b",
    fontSize: 13,
    fontWeight: "700"
  },
  metricValue: {
    color: "#0f172a",
    fontSize: 24,
    fontWeight: "700"
  }
});

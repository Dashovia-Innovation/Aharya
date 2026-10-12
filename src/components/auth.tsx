import { Image } from 'expo-image';
import { SymbolView } from 'expo-symbols';
import { StatusBar } from 'expo-status-bar';
import { useState, type ReactNode } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useColorScheme } from '@/hooks/use-color-scheme';

const brand = {
  teal: '#0F8B8D',
  leaf: '#6FC3BE',
  deep: '#0B4F55',
  white: '#FFFFFF',
  black: '#000000',
};

// Small text on white uses Deep: Teal on white is ~4.1:1, under the 4.5:1 AA minimum
const palettes = {
  dark: {
    ...brand,
    bg: brand.black,
    title: brand.teal,
    text: brand.teal,
    muted: 'rgba(255,255,255,0.7)',
    placeholder: 'rgba(255,255,255,0.5)',
    surface: 'rgba(255,255,255,0.08)',
    border: 'rgba(255,255,255,0.35)',
    link: brand.leaf,
    error: '#FFB4A9',
    buttonBg: brand.white,
    buttonText: brand.deep,
    socialBg: 'rgba(255,255,255,0.12)',
    socialText: brand.white,
    statusBar: 'light' as 'light' | 'dark',
  },
  light: {
    ...brand,
    bg: brand.white,
    title: brand.teal,
    text: brand.deep,
    muted: 'rgba(0,0,0,0.6)',
    placeholder: 'rgba(0,0,0,0.45)',
    surface: 'rgba(11,79,85,0.04)',
    border: 'rgba(0,0,0,0.45)',
    link: brand.deep,
    error: '#B42318',
    buttonBg: brand.deep,
    buttonText: brand.white,
    socialBg: '#F2F2F2',
    socialText: brand.black,
    statusBar: 'dark' as 'light' | 'dark',
  },
};

export type AuthPalette = typeof palettes.dark;

const makeStyles = (c: AuthPalette) =>
  StyleSheet.create({
    flex: { flex: 1, backgroundColor: c.bg },
    scroll: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 56, paddingBottom: 32 },
    title: { color: c.title, fontSize: 36, fontWeight: '700', lineHeight: 42 },
    subtitle: { color: c.muted, fontSize: 16, lineHeight: 24, marginTop: 12 },
    body: { marginTop: 32, gap: 16 },
    label: { color: c.text, fontSize: 14, fontWeight: '600', marginBottom: 6 },
    field: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingHorizontal: 14,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: c.border,
      backgroundColor: c.surface,
    },
    fieldError: { borderColor: c.error },
    input: { flex: 1, minHeight: 50, fontSize: 16, color: c.text },
    toggle: { minHeight: 44, minWidth: 44, justifyContent: 'center', alignItems: 'center' },
    link: { color: c.link, fontWeight: '600', fontSize: 15 },
    linkHit: { minHeight: 44, justifyContent: 'center', alignSelf: 'center' },
    error: { color: c.error, fontSize: 13, marginTop: 6 },
    button: {
      minHeight: 52,
      borderRadius: 999,
      backgroundColor: c.buttonBg,
      justifyContent: 'center',
      alignItems: 'center',
      marginTop: 8,
    },
    buttonText: { color: c.buttonText, fontSize: 17, fontWeight: '700' },
    pressed: { opacity: 0.8 },
    divider: { flexDirection: 'row', alignItems: 'center', gap: 12, marginVertical: 4 },
    line: { flex: 1, height: StyleSheet.hairlineWidth, backgroundColor: c.border },
    muted: { color: c.muted, fontSize: 15 },
    social: {
      minHeight: 52,
      borderRadius: 999,
      backgroundColor: c.socialBg,
      justifyContent: 'center',
      alignItems: 'center',
    },
    // Icon pinned left, label stays centred on the button
    brandLogo: { position: 'absolute', left: 22, width: 20, height: 20 },
    // Apple's glyph is taller than wide; nudge up so it sits optically centred
    appleLogo: { position: 'absolute', left: 23, width: 17, height: 20, top: 14 },
    socialText: { color: c.socialText, fontSize: 16, fontWeight: '500' },
    chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
    chip: {
      minHeight: 44,
      paddingHorizontal: 16,
      borderRadius: 999,
      borderWidth: 1,
      borderColor: c.border,
      backgroundColor: c.surface,
      justifyContent: 'center',
    },
    chipOn: { backgroundColor: c.buttonBg, borderColor: c.buttonBg },
    chipText: { color: c.text, fontSize: 15, fontWeight: '500' },
    chipTextOn: { color: c.buttonText, fontWeight: '600' },
    footer: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginTop: 8 },
  });

const themes = {
  dark: { c: palettes.dark, styles: makeStyles(palettes.dark) },
  light: { c: palettes.light, styles: makeStyles(palettes.light) },
};

/** Follows the device setting: black background in dark mode, white in light mode. */
export function useAuthTheme() {
  return themes[useColorScheme() === 'dark' ? 'dark' : 'light'];
}

export const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v.trim());

export function AuthScreen({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  const { c, styles } = useAuthTheme();
  return (
    <SafeAreaView style={styles.flex}>
      <StatusBar style={c.statusBar} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <Text style={styles.title} accessibilityRole="header">
            {title}
          </Text>
          {!!subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          <View style={styles.body}>{children}</View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

type FieldProps = TextInputProps & {
  label: string;
  icon?: 'mail' | 'lock';
  error?: string;
  secure?: boolean;
};

export function Field({ label, icon, error, secure, ...input }: FieldProps) {
  const { c, styles } = useAuthTheme();
  const [hidden, setHidden] = useState(true);
  return (
    <View>
      <Text style={styles.label}>{label}</Text>
      <View style={[styles.field, !!error && styles.fieldError]}>
        {icon && (
          <SymbolView
            accessible={false}
            importantForAccessibility="no"
            name={icon === 'mail' ? { ios: 'envelope', android: 'mail', web: 'mail' } : 'lock'}
            size={18}
            tintColor={c.muted}
          />
        )}
        <TextInput
          style={styles.input}
          accessibilityLabel={label}
          placeholderTextColor={c.placeholder}
          autoCapitalize="none"
          secureTextEntry={secure && hidden}
          {...input}
        />
        {secure && (
          <Pressable
            onPress={() => setHidden((h) => !h)}
            accessibilityRole="button"
            accessibilityLabel={hidden ? `Show ${label}` : `Hide ${label}`}
            style={styles.toggle}>
            <Text style={styles.link}>{hidden ? 'Show' : 'Hide'}</Text>
          </Pressable>
        )}
      </View>
      {!!error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

/** Pill choices. `multi` lets several be selected (checkbox), otherwise one (radio). */
export function Chips({
  label,
  options,
  selected,
  onChange,
  multi,
  error,
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
  multi?: boolean;
  error?: string;
}) {
  const { styles } = useAuthTheme();
  const toggle = (o: string) =>
    onChange(
      !multi ? [o] : selected.includes(o) ? selected.filter((x) => x !== o) : [...selected, o],
    );
  return (
    <View>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.chips} accessibilityRole={multi ? undefined : 'radiogroup'}>
        {options.map((o) => {
          const on = selected.includes(o);
          return (
            <Pressable
              key={o}
              onPress={() => toggle(o)}
              accessibilityRole={multi ? 'checkbox' : 'radio'}
              accessibilityState={{ checked: on }}
              style={({ pressed }) => [
                styles.chip,
                on && styles.chipOn,
                pressed && styles.pressed,
              ]}>
              <Text style={[styles.chipText, on && styles.chipTextOn]}>{o}</Text>
            </Pressable>
          );
        })}
      </View>
      {!!error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

export function PrimaryButton({ title, onPress }: { title: string; onPress: () => void }) {
  const { styles } = useAuthTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
      <Text style={styles.buttonText}>{title}</Text>
    </Pressable>
  );
}

export function SocialButtons() {
  const { c, styles } = useAuthTheme();
  // ponytail: OAuth not wired yet, add expo-auth-session / expo-apple-authentication when a backend exists
  const soon = () => Alert.alert('Coming soon', 'Social sign-in is not available yet.');
  return (
    <>
      <View style={styles.divider}>
        <View style={styles.line} />
        <Text style={styles.muted}>or</Text>
        <View style={styles.line} />
      </View>
      <Pressable
        onPress={soon}
        accessibilityRole="button"
        style={({ pressed }) => [styles.social, pressed && styles.pressed]}>
        <Image
          source={require('@/assets/images/brands/apple.svg')}
          style={styles.appleLogo}
          tintColor={c.socialText}
          contentFit="contain"
          accessible={false}
        />
        <Text style={styles.socialText}>Continue with Apple</Text>
      </Pressable>
      <Pressable
        onPress={soon}
        accessibilityRole="button"
        style={({ pressed }) => [styles.social, pressed && styles.pressed]}>
        <Image
          source={require('@/assets/images/brands/google.svg')}
          style={styles.brandLogo}
          contentFit="contain"
          accessible={false}
        />
        <Text style={styles.socialText}>Continue with Google</Text>
      </Pressable>
    </>
  );
}

export function FooterLink({
  text,
  action,
  onPress,
}: {
  text: string;
  action: string;
  onPress: () => void;
}) {
  const { styles } = useAuthTheme();
  return (
    <View style={styles.footer}>
      <Text style={styles.muted}>{text} </Text>
      <Pressable onPress={onPress} accessibilityRole="link" style={styles.toggle}>
        <Text style={styles.link}>{action}</Text>
      </Pressable>
    </View>
  );
}

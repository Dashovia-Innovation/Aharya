import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { AuthScreen, PrimaryButton, useAuthTheme } from '@/components/auth';

const LENGTH = 4;

export default function Verify() {
  const { c, styles: authStyles } = useAuthTheme();
  const { email, reset } = useLocalSearchParams<{ email?: string; reset?: string }>();
  const [code, setCode] = useState('');
  const [error, setError] = useState<string>();

  function onSubmit() {
    if (code.length !== LENGTH) return setError(`Enter the ${LENGTH}-digit code`);
    setError(undefined);
    // ponytail: no backend yet, any 4 digits pass; verify the code server-side here
    if (reset) router.push('/new-password');
    else router.replace('/home');
  }

  return (
    <AuthScreen
      title={'Verify\nYour Email'}
      subtitle={`Enter the ${LENGTH}-digit code sent to ${email || 'your email'}.`}>
      <View>
        {/* One invisible input over the boxes: native paste + SMS autofill for free */}
        <View style={styles.boxes}>
          {Array.from({ length: LENGTH }, (_, i) => (
            <View
              key={i}
              style={[
                styles.box,
                { borderColor: c.border, backgroundColor: c.surface },
                i === code.length && { borderColor: c.link, borderWidth: 2 },
                !!error && { borderColor: c.error },
              ]}>
              <Text style={[styles.digit, { color: c.text }]}>{code[i] ?? ''}</Text>
            </View>
          ))}
          <TextInput
            style={styles.hiddenInput}
            value={code}
            onChangeText={(t) => setCode(t.replace(/\D/g, '').slice(0, LENGTH))}
            keyboardType="number-pad"
            textContentType="oneTimeCode"
            autoComplete="one-time-code"
            maxLength={LENGTH}
            autoFocus
            accessibilityLabel="Verification code"
            onSubmitEditing={onSubmit}
          />
        </View>
        {!!error && <Text style={authStyles.error}>{error}</Text>}
      </View>
      <Pressable
        onPress={() => Alert.alert('Code sent', 'Check your inbox for a new code.')}
        accessibilityRole="button"
        style={authStyles.linkHit}>
        <Text style={authStyles.link}>Resend code</Text>
      </Pressable>
      <PrimaryButton title="Verify" onPress={onSubmit} />
    </AuthScreen>
  );
}

const styles = StyleSheet.create({
  boxes: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  box: {
    flex: 1,
    aspectRatio: 1,
    maxWidth: 72,
    borderRadius: 12,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  digit: { fontSize: 24, fontWeight: '700' },
  hiddenInput: { ...StyleSheet.absoluteFill, opacity: 0.01, color: 'transparent' },
});

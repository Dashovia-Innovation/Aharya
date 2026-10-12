import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text } from 'react-native';

import {
  AuthScreen,
  Field,
  FooterLink,
  isEmail,
  PrimaryButton,
  SocialButtons,
  useAuthTheme,
} from '@/components/auth';

export default function SignIn() {
  const { styles } = useAuthTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  function onSubmit() {
    const next = {
      email: isEmail(email) ? undefined : 'Enter a valid email address',
      password: password.length >= 6 ? undefined : 'Password must be at least 6 characters',
    };
    setErrors(next);
    if (next.email || next.password) return;
    // ponytail: no auth backend yet, wire real sign-in here
    router.replace('/home');
  }

  return (
    <AuthScreen title={'Hey,\nWelcome Back'} subtitle="Sign in to see your report insights.">
      <Field
        label="Email"
        icon="mail"
        placeholder="you@example.com"
        keyboardType="email-address"
        autoComplete="email"
        textContentType="emailAddress"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
      />
      <Field
        label="Password"
        icon="lock"
        secure
        placeholder="Your password"
        autoComplete="password"
        textContentType="password"
        value={password}
        onChangeText={setPassword}
        onSubmitEditing={onSubmit}
        error={errors.password}
      />
      <Pressable
        onPress={() => router.push('/forgot-password')}
        accessibilityRole="link"
        style={styles.linkHit}>
        <Text style={styles.link}>Forgot password?</Text>
      </Pressable>
      <PrimaryButton title="Sign in" onPress={onSubmit} />
      <SocialButtons />
      <FooterLink
        text="Don't have an account?"
        action="Sign up"
        onPress={() => router.dismissTo('/sign-up')}
      />
    </AuthScreen>
  );
}

import { router } from 'expo-router';
import { useState } from 'react';

import {
  AuthScreen,
  Field,
  FooterLink,
  isEmail,
  PrimaryButton,
  SocialButtons,
} from '@/components/auth';

export default function SignUp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string; confirm?: string }>({});

  function onSubmit() {
    const next = {
      email: isEmail(email) ? undefined : 'Enter a valid email address',
      password: password.length >= 6 ? undefined : 'Password must be at least 6 characters',
      confirm: confirm === password ? undefined : 'Passwords do not match',
    };
    setErrors(next);
    if (next.email || next.password || next.confirm) return;
    router.push({ pathname: '/verify', params: { email } });
  }

  return (
    <AuthScreen title={"Let's get\nStarted"} subtitle="Create an account to analyse your reports.">
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
        placeholder="At least 6 characters"
        autoComplete="new-password"
        textContentType="newPassword"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
      />
      <Field
        label="Confirm password"
        icon="lock"
        secure
        placeholder="Re-enter password"
        autoComplete="new-password"
        textContentType="newPassword"
        value={confirm}
        onChangeText={setConfirm}
        onSubmitEditing={onSubmit}
        error={errors.confirm}
      />
      <PrimaryButton title="Sign up" onPress={onSubmit} />
      <SocialButtons />
      <FooterLink
        text="Already have an account?"
        action="Login"
        onPress={() => router.push('/sign-in')}
      />
    </AuthScreen>
  );
}

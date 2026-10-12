import { router } from 'expo-router';
import { useState } from 'react';

import { AuthScreen, Field, isEmail, PrimaryButton } from '@/components/auth';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string>();

  function onSubmit() {
    if (!isEmail(email)) return setError('Enter a valid email address');
    setError(undefined);
    router.push({ pathname: '/verify', params: { email, reset: '1' } });
  }

  return (
    <AuthScreen title={'Forgot\nPassword?'} subtitle="Enter your email and we'll send you a code.">
      <Field
        label="Email"
        icon="mail"
        placeholder="you@example.com"
        keyboardType="email-address"
        autoComplete="email"
        textContentType="emailAddress"
        value={email}
        onChangeText={setEmail}
        onSubmitEditing={onSubmit}
        error={error}
      />
      <PrimaryButton title="Send" onPress={onSubmit} />
    </AuthScreen>
  );
}

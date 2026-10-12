import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { AuthScreen, Chips, Field, PrimaryButton, useAuthTheme } from '@/components/auth';

const SEX = ['Female', 'Male', 'Other'];
const DIETS = ['Vegetarian', 'Eggetarian', 'Non-vegetarian', 'Vegan'];
const CONDITIONS = [
  'Diabetes',
  'Thyroid',
  'Blood pressure',
  'Cholesterol',
  'PCOS',
  'Kidney',
  'None',
];

const inRange = (v: string, min: number, max: number) => {
  const n = Number(v);
  return v.trim() !== '' && n >= min && n <= max;
};

type Errors = Partial<Record<'name' | 'age' | 'sex' | 'height' | 'weight' | 'diet', string>>;

export default function Onboarding() {
  const { styles } = useAuthTheme();
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<string[]>([]);
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [diet, setDiet] = useState<string[]>([]);
  const [conditions, setConditions] = useState<string[]>([]);
  const [allergies, setAllergies] = useState('');
  const [errors, setErrors] = useState<Errors>({});

  // "None" is exclusive: picking it clears the rest, picking anything else clears it
  function onConditions(next: string[]) {
    const added = next.find((x) => !conditions.includes(x));
    if (added === 'None') return setConditions(['None']);
    setConditions(next.filter((x) => x !== 'None'));
  }

  function onSubmit() {
    const next: Errors = {
      name: name.trim() ? undefined : 'Enter your name',
      age: inRange(age, 1, 120) ? undefined : 'Enter an age between 1 and 120',
      sex: sex.length ? undefined : 'Select one',
      height: inRange(height, 50, 250) ? undefined : '50–250 cm',
      weight: inRange(weight, 10, 300) ? undefined : '10–300 kg',
      diet: diet.length ? undefined : 'Select your diet',
    };
    setErrors(next);
    if (Object.values(next).some(Boolean)) return;
    // ponytail: no backend yet, save { name, age, sex, height, weight, diet, conditions, allergies } here
    router.replace('/home');
  }

  return (
    <AuthScreen
      title={'Tell us\nAbout You'}
      subtitle="This helps us read your reports accurately and build a diet plan that fits you.">
      <Field
        label="Full name"
        placeholder="Your name"
        autoCapitalize="words"
        autoComplete="name"
        textContentType="name"
        value={name}
        onChangeText={setName}
        error={errors.name}
      />
      <Field
        label="Age"
        placeholder="Years"
        keyboardType="number-pad"
        maxLength={3}
        value={age}
        onChangeText={setAge}
        error={errors.age}
      />
      <Chips label="Sex" options={SEX} selected={sex} onChange={setSex} error={errors.sex} />
      <View style={local.row}>
        <View style={local.half}>
          <Field
            label="Height (cm)"
            placeholder="170"
            keyboardType="decimal-pad"
            maxLength={5}
            value={height}
            onChangeText={setHeight}
            error={errors.height}
          />
        </View>
        <View style={local.half}>
          <Field
            label="Weight (kg)"
            placeholder="65"
            keyboardType="decimal-pad"
            maxLength={5}
            value={weight}
            onChangeText={setWeight}
            error={errors.weight}
          />
        </View>
      </View>
      <Chips
        label="Diet preference"
        options={DIETS}
        selected={diet}
        onChange={setDiet}
        error={errors.diet}
      />
      <Chips
        label="Health conditions (optional)"
        options={CONDITIONS}
        selected={conditions}
        onChange={onConditions}
        multi
      />
      <Field
        label="Food allergies (optional)"
        placeholder="e.g. peanuts, lactose"
        autoCapitalize="sentences"
        value={allergies}
        onChangeText={setAllergies}
      />
      <PrimaryButton title="Continue" onPress={onSubmit} />
      <Pressable
        onPress={() => router.replace('/home')}
        accessibilityRole="button"
        style={styles.linkHit}>
        <Text style={styles.link}>Skip for now</Text>
      </Pressable>
    </AuthScreen>
  );
}

const local = StyleSheet.create({
  row: { flexDirection: 'row', gap: 12 },
  half: { flex: 1 },
});

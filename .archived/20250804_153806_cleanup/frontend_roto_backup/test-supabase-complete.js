const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Cargar variables de entorno desde .env.local
dotenv.config({ path: path.join(__dirname, '.env.local') });

console.log('🔍 Testing Supabase Configuration...\n');

// 1. Verificar variables de entorno
console.log('1. Variables de entorno:');
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

console.log('   URL:', supabaseUrl ? '✅ Configurada' : '❌ Faltante');
console.log('   Key:', supabaseKey ? '✅ Configurada' : '❌ Faltante');

if (!supabaseUrl || !supabaseKey) {
  console.log('\n❌ Error: Variables de entorno faltantes');
  process.exit(1);
}

// 2. Crear cliente de Supabase
console.log('\n2. Creando cliente Supabase...');
const supabase = createClient(supabaseUrl, supabaseKey);
console.log('   ✅ Cliente creado exitosamente');

// 3. Test de conectividad
async function testConnection() {
  console.log('\n3. Probando conectividad...');
  try {
    const { data, error } = await supabase
      .from('tenants')
      .select('count')
      .limit(1);
    
    if (error) {
      console.log('   ❌ Error de conectividad:', error.message);
      return false;
    }
    
    console.log('   ✅ Conectividad exitosa');
    return true;
  } catch (err) {
    console.log('   ❌ Error de red:', err.message);
    return false;
  }
}

// 4. Test de autenticación
async function testAuth() {
  console.log('\n4. Probando autenticación...');
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: 'felipe@tause.co',
      password: 'test123456'
    });
    
    if (error) {
      console.log('   ❌ Error de autenticación:', error.message);
      return false;
    }
    
    console.log('   ✅ Login exitoso');
    console.log('   Usuario:', data.user.email);
    console.log('   Confirmado:', data.user.email_confirmed_at ? 'Sí' : 'No');
    
    // Logout
    await supabase.auth.signOut();
    console.log('   ✅ Logout exitoso');
    
    return true;
  } catch (err) {
    console.log('   ❌ Error de autenticación:', err.message);
    return false;
  }
}

// 5. Test de tablas
async function testTables() {
  console.log('\n5. Verificando tablas...');
  
  try {
    // Test tabla tenants
    const { data: tenants, error: tenantsError } = await supabase
      .from('tenants')
      .select('*')
      .limit(5);
    
    if (tenantsError) {
      console.log('   ❌ Error en tabla tenants:', tenantsError.message);
    } else {
      console.log('   ✅ Tabla tenants:', tenants.length, 'registros');
    }
    
    // Test tabla users
    const { data: users, error: usersError } = await supabase
      .from('users')
      .select('*')
      .limit(5);
    
    if (usersError) {
      console.log('   ❌ Error en tabla users:', usersError.message);
    } else {
      console.log('   ✅ Tabla users:', users.length, 'registros');
    }
    
    return !tenantsError && !usersError;
  } catch (err) {
    console.log('   ❌ Error verificando tablas:', err.message);
    return false;
  }
}

// Ejecutar todos los tests
async function runAllTests() {
  const connectivityOk = await testConnection();
  const authOk = await testAuth();
  const tablesOk = await testTables();
  
  console.log('\n📊 Resumen de Tests:');
  console.log('   Conectividad:', connectivityOk ? '✅' : '❌');
  console.log('   Autenticación:', authOk ? '✅' : '❌');
  console.log('   Tablas:', tablesOk ? '✅' : '❌');
  
  if (connectivityOk && authOk && tablesOk) {
    console.log('\n🎉 ¡Toda la configuración de Supabase está perfecta!');
    console.log('\n🚀 Puedes usar las credenciales:');
    console.log('   Email: felipe@tause.co');
    console.log('   Password: test123456');
  } else {
    console.log('\n⚠️  Hay problemas en la configuración que necesitan revisión.');
  }
}

runAllTests().catch(console.error); 
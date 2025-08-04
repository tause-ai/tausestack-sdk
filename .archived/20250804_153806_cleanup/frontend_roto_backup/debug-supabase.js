// Script de debug para probar Supabase
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://vjoxmprmcbkmhwmbniaz.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.bY4FrlKtDK2TnMt7hOC5_KpIuoHwqJLOYkB-bWs_Wd8';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  console.log('🔧 Testing Supabase connection...');
  
  try {
    // Test basic connection
    const { data, error } = await supabase.from('tenants').select('*');
    if (error) {
      console.error('❌ Error connecting to tenants table:', error);
    } else {
      console.log('✅ Connected to tenants table:', data);
    }
    
    // Test auth
    console.log('\n🔐 Testing authentication...');
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email: 'felipe@tause.co',
      password: 'test123'
    });
    
    if (authError) {
      console.error('❌ Auth error:', authError.message);
    } else {
      console.log('✅ Auth successful:', authData);
    }
    
  } catch (err) {
    console.error('❌ General error:', err);
  }
}

testConnection(); 
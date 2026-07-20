package com.xenglish.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.xenglish.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "xenglish_config")

/** Config persistente: URL del backend y API key (single-user). */
class AppConfig(private val context: Context) {

    private val baseUrlKey = stringPreferencesKey("base_url")
    private val apiKeyKey = stringPreferencesKey("api_key")

    val baseUrl: Flow<String> = context.dataStore.data.map {
        it[baseUrlKey] ?: BuildConfig.DEFAULT_BASE_URL
    }
    val apiKey: Flow<String> = context.dataStore.data.map { it[apiKeyKey] ?: BuildConfig.DEFAULT_API_KEY }

    suspend fun setBaseUrl(value: String) =
        context.dataStore.edit { it[baseUrlKey] = value }

    suspend fun setApiKey(value: String) =
        context.dataStore.edit { it[apiKeyKey] = value }
}

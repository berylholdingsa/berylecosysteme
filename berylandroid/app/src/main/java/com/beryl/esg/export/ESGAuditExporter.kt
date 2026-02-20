package com.beryl.esg.export

import android.content.Context
import java.io.File
import java.io.FileWriter

class ESGAuditExporter(private val context: Context) {

    fun exportToCSV(record: ESGAuditRecord): File {
        val fileName = "audit_esg_${System.currentTimeMillis()}.csv"
        val file = File(context.filesDir, fileName)

        FileWriter(file).use { writer ->
            writer.append("Ville,Période,KmVerts,CO2EviteKg,ScoreESG,ClasseImpact,MessageAOQ\n")
            writer.append(
                "${record.ville}," +
                "${record.periode}," +
                "${record.kmVerts}," +
                "${record.co2EviteKg}," +
                "${record.scoreEsg}," +
                "${record.classeImpact}," +
                "\"${record.messageAoq}\"\n"
            )
        }

        return file
    }

    fun generatePdfStructure(record: ESGAuditRecord): String {
        return """
            RAPPORT D’IMPACT ESG

            Ville : ${record.ville}
            Période : ${record.periode}

            Km verts : ${record.kmVerts}
            CO₂ évité : ${record.co2EviteKg} kg

            Score ESG : ${record.scoreEsg}
            Classe d’impact : ${record.classeImpact}

            Message IA AOQ :
            ${record.messageAoq}

            ---  
            Document généré par le moteur ESG piloté par IA.
        """.trimIndent()
    }
}

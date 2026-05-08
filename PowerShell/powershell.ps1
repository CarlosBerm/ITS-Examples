#Error handling
$ErrorActionPreference = "SilentlyContinue"
$Error.clear()

#U-M GPT required parameters
$API_BASE = "" #API endpoint url
$DEPLOYMENT_ID = "" #chat deployment model name
$API_KEY = "" #API key 
$MESSAGES =  @{role="system";content="You are a helpful bot"},@{role="user";content="What is 2+2"} #chat message

#Build the request
$uri = "$($API_BASE)/openai/deployments/$($DEPLOYMENT_ID)/chat/completions?api-version=$($API_VERSION)"

$headers = @{"Content-Type" = "application/json"}
$headers += @{"api-key" = $API_KEY}

$body = @{
    model = $DEPLOYMENT_ID
    messages = $MESSAGES

    #Examples of optional request body parameters
    #Please review the Azure OpenAI Service REST API reference for documentation and examples

    #temperature = 0
    #max_tokens = 350
    #top_p = 0.95
    #frequency_penalty = 0
    #presence_penalty = 0

} | ConvertTo-Json

#submit the request
try {
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body

    #Write the response the console
    Write-Host $response.choices.message.content
}
catch {
    Write-Host "An error occured."
    Write-Host $Error
}

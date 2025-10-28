# Push to GitHub - Step by Step Instructions

## Step 1: Create the Repository on GitHub

1. Go to: https://github.com/new
2. Repository name: `RandWaterCompensation`
3. Description: "Rand Water Salary Calculator - TCTC Modeling System"
4. **Make it Private** (recommended for internal use)
5. **DO NOT** check "Add a README file"
6. **DO NOT** check "Add .gitignore"
7. **DO NOT** check "Choose a license"
8. Click **"Create repository"**

## Step 2: After Creating the Repository, Run These Commands

Open PowerShell in your project directory and run:

```powershell
git push -u origin main
```

When prompted for credentials:
- **Username**: annelise@smarthr.co.za
- **Password**: $m@rtHR7

## Alternative: If Authentication Fails

If the push fails due to authentication, you can try these options:

### Option A: Use Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token"
3. Select scope: **repo** (all checkboxes under repo)
4. Generate token and copy it
5. Use the token as password when pushing

### Option B: Use GitHub CLI
```powershell
gh auth login
```

### Option C: Manual Authentication in URL
```powershell
git push https://annelise@smarthr.co.za:YOUR_TOKEN@github.com/smarthrdev/RandWaterCompensation.git main
```

## Step 3: Verify

After successful push, go to:
https://github.com/smarthrdev/RandWaterCompensation

You should see all your files uploaded!

